from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user
from app.db import get_db
from app.models import MailboxResponse, MessageResponse

router = APIRouter()


@router.get("/api/mailboxes", response_model=List[MailboxResponse])
async def list_mailboxes(user: dict = Depends(get_current_user)):
    db = await get_db()
    rows = await db.fetchall(
        "SELECT id, name, special_use, uidnext FROM mailboxes WHERE user_id = ?",
        (user["id"],),
    )
    return [dict(row) for row in rows]


@router.get("/api/mailboxes/{mailbox_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    mailbox_id: int,
    cursor: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    db = await get_db()
    mailbox = await db.fetchone(
        "SELECT id FROM mailboxes WHERE id = ? AND user_id = ?",
        (mailbox_id, user["id"]),
    )
    if mailbox is None:
        raise HTTPException(status_code=404, detail="Mailbox not found")

    if cursor:
        rows = await db.fetchall(
            """
            SELECT m.id, m.uid, m.message_id, m.subject, m.from_addr, m.to_addr,
                   m.date, m.size, m.flags,
                   EXISTS(SELECT 1 FROM attachments a WHERE a.message_id = m.id) as has_attachments
            FROM messages m
            WHERE m.mailbox_id = ? AND m.id < ?
            ORDER BY m.id DESC
            LIMIT ?
            """,
            (mailbox_id, cursor, limit),
        )
    else:
        rows = await db.fetchall(
            """
            SELECT m.id, m.uid, m.message_id, m.subject, m.from_addr, m.to_addr,
                   m.date, m.size, m.flags,
                   EXISTS(SELECT 1 FROM attachments a WHERE a.message_id = m.id) as has_attachments
            FROM messages m
            WHERE m.mailbox_id = ?
            ORDER BY m.id DESC
            LIMIT ?
            """,
            (mailbox_id, limit),
        )

    messages = []
    for row in rows:
        msg = dict(row)
        msg["flags"] = [f.strip() for f in (msg["flags"] or "").split(",") if f.strip()]
        if msg["date"]:
            msg["date"] = datetime.fromtimestamp(msg["date"], timezone.utc)
        messages.append(msg)
    return messages
