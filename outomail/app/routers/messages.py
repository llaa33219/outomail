import json
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user
from app.config import get_settings
from app.db import get_db
from app.dns.dkim import DKIMManager
from app.models import MessageCreate, MessageDetail, MessageResponse, SearchResult
from app.smtp.delivery import SMTPDelivery
from app.storage.messages import MessageStorage

router = APIRouter()


def _get_delivery():
    settings = get_settings()
    dkim = DKIMManager(
        domain=settings.DOMAIN,
        selector=settings.DKIM_SELECTOR,
        key_path=settings.DKIM_KEY_PATH,
    )
    return SMTPDelivery(dkim)


@router.get("/api/messages/{message_id}", response_model=MessageDetail)
async def get_message(message_id: int, user: dict = Depends(get_current_user)):
    db = await get_db()
    row = await db.fetchone(
        """
        SELECT m.id, m.uid, m.message_id, m.subject, m.from_addr, m.to_addr,
               m.date, m.size, m.flags, m.headers, m.body_text, m.body_html,
               EXISTS(SELECT 1 FROM attachments a WHERE a.message_id = m.id) as has_attachments
        FROM messages m
        JOIN mailboxes mb ON m.mailbox_id = mb.id
        WHERE m.id = ? AND mb.user_id = ?
        """,
        (message_id, user["id"]),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Message not found")

    msg = dict(row)
    msg["flags"] = [f.strip() for f in (msg["flags"] or "").split(",") if f.strip()]
    if msg["date"]:
        msg["date"] = datetime.fromtimestamp(msg["date"], timezone.utc)

    headers = {}
    if msg.get("headers"):
        try:
            headers = json.loads(msg["headers"])
        except json.JSONDecodeError:
            pass
    msg["headers"] = headers

    att_rows = await db.fetchall(
        "SELECT id, filename, content_type, size, content_id, disposition FROM attachments WHERE message_id = ?",
        (message_id,),
    )
    msg["attachments"] = [dict(a) for a in att_rows]

    return msg


@router.post("/api/messages", response_model=MessageResponse, status_code=201)
async def send_message(body: MessageCreate, user: dict = Depends(get_current_user)):
    settings = get_settings()
    db = await get_db()

    msg = EmailMessage()
    msg["From"] = user["email"]
    msg["To"] = body.to
    msg["Subject"] = body.subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=settings.DOMAIN)
    if body.cc:
        msg["Cc"] = body.cc

    if body.html:
        msg.set_content(body.body)
        msg.add_alternative(body.html, subtype="html")
    else:
        msg.set_content(body.body)

    raw_bytes = msg.as_bytes()

    delivery = _get_delivery()
    success = await delivery.deliver(raw_bytes, user["email"], body.to)
    if not success:
        raise HTTPException(status_code=502, detail="Failed to deliver message")

    sent_mbox = await db.fetchone(
        "SELECT id, uidnext FROM mailboxes WHERE user_id = ? AND name = ?",
        (user["id"], "Sent"),
    )
    if sent_mbox is None:
        cursor = await db.execute(
            "INSERT INTO mailboxes (user_id, name, uidnext) VALUES (?, ?, ?)",
            (user["id"], "Sent", 1),
        )
        sent_mbox_id = cursor.lastrowid
        sent_uid = 1
        await db.execute(
            "UPDATE mailboxes SET uidnext = uidnext + 1 WHERE id = ?",
            (sent_mbox_id,),
        )
    else:
        sent_mbox_id = sent_mbox["id"]
        sent_uid = sent_mbox["uidnext"]
        await db.execute(
            "UPDATE mailboxes SET uidnext = uidnext + 1 WHERE id = ?",
            (sent_mbox_id,),
        )

    date_ts = int(datetime.now(timezone.utc).timestamp())
    headers_dict = {k: msg[k] for k in msg.keys()}

    await db.execute(
        """
        INSERT INTO messages (
            mailbox_id, uid, message_id, subject, from_addr, to_addr,
            cc_addr, date, size, flags, headers, body_text, body_html
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sent_mbox_id,
            sent_uid,
            msg["Message-ID"],
            body.subject,
            user["email"],
            body.to,
            body.cc or "",
            date_ts,
            len(raw_bytes),
            "\\Seen",
            json.dumps(headers_dict),
            body.body,
            body.html,
        ),
    )

    message_row = await db.fetchone("SELECT last_insert_rowid() as id")
    message_db_id = message_row["id"]

    storage = MessageStorage(settings.MAIL_STORAGE_PATH)
    username = user["email"].split("@")[0]
    await storage.save(username, "Sent", sent_uid, raw_bytes)

    return {
        "id": message_db_id,
        "uid": sent_uid,
        "message_id": msg["Message-ID"],
        "subject": body.subject,
        "from_addr": user["email"],
        "to_addr": body.to,
        "date": datetime.fromtimestamp(date_ts, timezone.utc),
        "size": len(raw_bytes),
        "flags": ["\\Seen"],
        "has_attachments": False,
    }


@router.delete("/api/messages/{message_id}", status_code=204)
async def delete_message(message_id: int, user: dict = Depends(get_current_user)):
    db = await get_db()
    row = await db.fetchone(
        """
        SELECT m.uid, mb.name, u.email
        FROM messages m
        JOIN mailboxes mb ON m.mailbox_id = mb.id
        JOIN users u ON mb.user_id = u.id
        WHERE m.id = ? AND mb.user_id = ?
        """,
        (message_id, user["id"]),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Message not found")

    storage = MessageStorage(get_settings().MAIL_STORAGE_PATH)
    username = row["email"].split("@")[0]
    await storage.delete(username, row["name"], row["uid"])

    await db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    return None


@router.post("/api/messages/{message_id}/read", status_code=204)
async def mark_read(message_id: int, user: dict = Depends(get_current_user)):
    db = await get_db()
    row = await db.fetchone(
        """
        SELECT m.flags
        FROM messages m
        JOIN mailboxes mb ON m.mailbox_id = mb.id
        WHERE m.id = ? AND mb.user_id = ?
        """,
        (message_id, user["id"]),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Message not found")

    flags = [f.strip() for f in (row["flags"] or "").split(",") if f.strip()]
    if "\\Seen" not in flags:
        flags.append("\\Seen")
        flag_str = ",".join(flags)
        await db.execute(
            "UPDATE messages SET flags = ? WHERE id = ?",
            (flag_str, message_id),
        )
    return None


@router.get("/api/search", response_model=List[SearchResult])
async def search_messages(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    db = await get_db()
    rows = await db.fetchall(
        """
        SELECT m.message_id, m.subject, m.from_addr, m.date,
               snippet(messages_fts, 1, '<mark>', '</mark>', '...', 32) as snippet,
               -bm25(messages_fts) as rank
        FROM messages_fts
        JOIN messages m ON messages_fts.rowid = m.id
        JOIN mailboxes mb ON m.mailbox_id = mb.id
        WHERE messages_fts MATCH ? AND mb.user_id = ?
        ORDER BY rank DESC
        LIMIT ?
        """,
        (q, user["id"], limit),
    )
    results = []
    for row in rows:
        r = dict(row)
        if r["date"]:
            r["date"] = datetime.fromtimestamp(r["date"], timezone.utc)
        results.append(r)
    return results

