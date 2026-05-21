import email
import email.policy
import json
from datetime import datetime, timezone

from aiosmtpd.smtp import Envelope, Session, SMTP

from app.config import get_settings
from app.db import Database
from app.storage.messages import MessageStorage


class MailHandler:
    def __init__(self, db_path: str | None = None, storage: MessageStorage | None = None) -> None:
        self._db_path = db_path
        self._db: Database | None = None
        self._storage = storage

    async def _get_db(self) -> Database:
        if self._db is None:
            if self._db_path:
                self._db = Database(self._db_path)
            else:
                self._db = Database(get_settings().DATABASE_PATH)
            await self._db.connect()
        return self._db

    async def _get_storage(self) -> MessageStorage:
        if self._storage is None:
            self._storage = MessageStorage(get_settings().MAIL_STORAGE_PATH)
        return self._storage

    async def handle_RCPT(self, server: SMTP, session: Session, envelope: Envelope, address: str, rcpt_options: list) -> str | None:
        settings = get_settings()
        domain = address.split("@")[-1].lower()
        if domain != settings.DOMAIN.lower():
            return "550 Relay not permitted"
        db = await self._get_db()
        user = await db.fetchone("SELECT id FROM users WHERE email = ? AND is_active = 1", (address,))
        if user is None:
            user = await db.fetchone("SELECT id FROM users WHERE LOWER(email) = ? AND is_active = 1", (address.lower(),))
        if user is None:
            return "550 User unknown"
        return None

    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope) -> str:
        db = await self._get_db()
        storage = await self._get_storage()
        msg = email.message_from_bytes(envelope.content, policy=email.policy.default)

        subject = msg.get("Subject", "")
        from_addr = msg.get("From", "")
        message_id = msg.get("Message-ID", "")
        date_hdr = msg.get("Date")
        date_ts = None
        if date_hdr:
            try:
                parsed_date = email.utils.parsedate_to_datetime(date_hdr)
                date_ts = int(parsed_date.timestamp())
            except Exception:
                pass
        if date_ts is None:
            date_ts = int(datetime.now(timezone.utc).timestamp())

        headers_dict = {}
        for key in msg.keys():
            headers_dict[key] = msg.get(key, "")

        body_text = None
        body_html = None
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = part.get("Content-Disposition", "")
                if "attachment" in disposition or part.get_filename():
                    filename = part.get_filename() or "unnamed"
                    payload = part.get_payload(decode=True) or b""
                    attachments.append({
                        "filename": filename,
                        "content_type": content_type,
                        "size": len(payload),
                        "content_id": part.get("Content-ID", ""),
                        "disposition": disposition.split(";")[0] if disposition else "attachment",
                    })
                elif content_type == "text/plain" and body_text is None:
                    body_text = part.get_content()
                elif content_type == "text/html" and body_html is None:
                    body_html = part.get_content()
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                body_text = msg.get_content()
            elif content_type == "text/html":
                body_html = msg.get_content()

        for rcpt in envelope.rcpt_tos:
            user = await db.fetchone(
                "SELECT id, email FROM users WHERE email = ? AND is_active = 1",
                (rcpt,)
            )
            if user is None:
                user = await db.fetchone(
                    "SELECT id, email FROM users WHERE LOWER(email) = ? AND is_active = 1",
                    (rcpt.lower(),)
                )
            if user is None:
                continue

            mailbox = await db.fetchone(
                "SELECT id, uidnext FROM mailboxes WHERE user_id = ? AND name = ?",
                (user["id"], "INBOX")
            )
            if mailbox is None:
                continue

            uid = mailbox["uidnext"]
            await db.execute(
                "UPDATE mailboxes SET uidnext = uidnext + 1 WHERE id = ?",
                (mailbox["id"],)
            )

            await db.execute(
                """INSERT INTO messages (
                    mailbox_id, uid, message_id, subject, from_addr, to_addr,
                    cc_addr, date, size, flags, headers, body_text, body_html
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    mailbox["id"],
                    uid,
                    message_id,
                    subject,
                    from_addr,
                    rcpt,
                    msg.get("Cc", ""),
                    date_ts,
                    len(envelope.content),
                    "",
                    json.dumps(headers_dict),
                    body_text,
                    body_html,
                )
            )

            message_row = await db.fetchone("SELECT last_insert_rowid() as id")
            message_db_id = message_row["id"]

            username = user["email"].split("@")[0]
            await storage.save(username, "INBOX", uid, envelope.content)

            for att in attachments:
                await db.execute(
                    """INSERT INTO attachments (
                        message_id, filename, content_type, size,
                        content_id, disposition
                    ) VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        message_db_id,
                        att["filename"],
                        att["content_type"],
                        att["size"],
                        att["content_id"],
                        att["disposition"],
                    )
                )

        return "250 OK"
