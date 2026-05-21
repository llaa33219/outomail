from __future__ import annotations

from collections.abc import AsyncIterable, Iterable
from datetime import datetime, timezone

from pymap.context import subsystem
from pymap.flags import FlagOp
from pymap.interfaces.message import CachedMessage
from pymap.listtree import ListTree
from pymap.mailbox import MailboxSnapshot
from pymap.message import BaseMessage, BaseLoadedMessage
from pymap.mime import MessageContent
from pymap.parsing.message import AppendMessage
from pymap.parsing.specials import ObjectId, FetchRequirement
from pymap.parsing.specials.flag import Flag, Seen, Recent
from pymap.selected import SelectedSet, SelectedMailbox
from pymap.backend.mailbox import MailboxDataInterface, MailboxSetInterface

from app.config import get_settings
from app.db import get_db
from app.storage.messages import MessageStorage


class SQLiteMessage(BaseMessage):
    __slots__ = ["_recent", "_content", "_raw"]

    def __init__(self, uid: int, internal_date: datetime,
                 permanent_flags: Iterable[Flag], *, expunged: bool = False,
                 email_id: ObjectId | None = None,
                 thread_id: ObjectId | None = None,
                 recent: bool = False,
                 content: MessageContent | None = None,
                 raw: bytes | None = None) -> None:
        super().__init__(uid, internal_date, permanent_flags,
                         expunged=expunged, email_id=email_id,
                         thread_id=thread_id)
        self._recent = recent
        self._content = content
        self._raw = raw

    @classmethod
    def copy(cls, msg: SQLiteMessage, *, uid: int | None = None,
             recent: bool = False, expunged: bool = False) -> SQLiteMessage:
        if uid is None:
            uid = msg.uid
        return cls(uid, msg.internal_date, msg.permanent_flags,
                   expunged=expunged, email_id=msg.email_id,
                   thread_id=msg.thread_id, recent=recent,
                   content=msg._content, raw=msg._raw)

    @property
    def recent(self) -> bool:
        return self._recent

    @recent.setter
    def recent(self, recent: bool) -> None:
        self._recent = recent

    async def load_content(self, requirement: FetchRequirement):
        return SQLiteLoadedMessage(self, requirement, self._content)


class SQLiteLoadedMessage(BaseLoadedMessage):
    pass


class SQLiteMailboxData(MailboxDataInterface[SQLiteMessage]):
    def __init__(self, user_id: int, username: str, mailbox_name: str,
                 mailbox_db_id: int, uidvalidity: int, uidnext: int) -> None:
        self._mailbox_id = ObjectId.random_mailbox_id()
        self._user_id = user_id
        self._username = username
        self._mailbox_name = mailbox_name
        self._mailbox_db_id = mailbox_db_id
        self._uid_validity = uidvalidity
        self._uid_next = uidnext
        self._readonly = False
        self._updated = subsystem.get().new_event()
        self._messages_lock = subsystem.get().new_rwlock()
        self._selected_set = SelectedSet()
        self._messages: dict[int, SQLiteMessage] = {}

    @property
    def mailbox_id(self) -> ObjectId:
        return self._mailbox_id

    @property
    def readonly(self) -> bool:
        return self._readonly

    @property
    def uid_validity(self) -> int:
        return self._uid_validity

    @property
    def messages_lock(self):
        return self._messages_lock

    @property
    def selected_set(self) -> SelectedSet:
        return self._selected_set

    async def _load_messages(self) -> None:
        db = await get_db()
        rows = await db.fetchall(
            "SELECT uid, date, flags FROM messages WHERE mailbox_id = ? ORDER BY uid",
            (self._mailbox_db_id,),
        )
        self._messages = {}
        storage = MessageStorage(get_settings().MAIL_STORAGE_PATH)
        for row in rows:
            uid = row["uid"]
            raw = await storage.read(self._username, self._mailbox_name, uid)
            content = MessageContent.parse(raw) if raw else None
            flags = {Flag(f.strip()) for f in (row["flags"] or "").split(",") if f.strip()}
            recent = Recent in flags
            if recent:
                flags.discard(Recent)
            dt = datetime.fromtimestamp(row["date"], timezone.utc) if row["date"] else datetime.now(timezone.utc)
            msg = SQLiteMessage(
                uid, dt, flags, recent=recent, content=content, raw=raw
            )
            self._messages[uid] = msg

    async def update_selected(self, selected: SelectedMailbox, *,
                              wait_on=None) -> SelectedMailbox:
        if wait_on is not None:
            either_event = wait_on.or_event(self._updated)
            await either_event.wait()
        await self._load_messages()
        all_messages = list(self._messages.values())
        selected.add_updates(all_messages, [])
        return selected

    async def append(self, append_msg: AppendMessage, *,
                     recent: bool = False) -> SQLiteMessage:
        db = await get_db()
        when = append_msg.when or datetime.now(timezone.utc)
        content = MessageContent.parse(append_msg.literal)
        async with self.messages_lock.write_lock():
            new_uid = self._uid_next
            self._uid_next += 1
            await db.execute(
                "UPDATE mailboxes SET uidnext = ? WHERE id = ?",
                (self._uid_next, self._mailbox_db_id),
            )
            flag_str = ",".join(str(f) for f in append_msg.flag_set)
            await db.execute(
                "INSERT INTO messages (mailbox_id, uid, date, size, flags) VALUES (?, ?, ?, ?, ?)",
                (self._mailbox_db_id, new_uid, int(when.timestamp()),
                 len(append_msg.literal), flag_str),
            )
            storage = MessageStorage(get_settings().MAIL_STORAGE_PATH)
            await storage.save(self._username, self._mailbox_name, new_uid,
                               append_msg.literal)
            msg = SQLiteMessage(
                new_uid, when, append_msg.flag_set,
                recent=recent, content=content, raw=append_msg.literal
            )
            self._messages[new_uid] = msg
            self._updated.set()
            return msg

    async def copy(self, uid: int, destination, *,
                   recent: bool = False) -> int | None:
        async with self.messages_lock.read_lock():
            msg = self._messages.get(uid)
        if msg is None:
            return None
        return await destination.append(
            AppendMessage(msg._raw or b"", msg.internal_date,
                          msg.permanent_flags),
            recent=recent,
        )

    async def move(self, uid: int, destination, *,
                   recent: bool = False) -> int | None:
        async with self.messages_lock.write_lock():
            msg = self._messages.pop(uid, None)
            if msg is None:
                return None
            self._updated.set()
        return await destination.append(
            AppendMessage(msg._raw or b"", msg.internal_date,
                          msg.permanent_flags),
            recent=recent,
        )

    async def get(self, uid: int, cached_msg: CachedMessage) -> SQLiteMessage:
        if uid < 1:
            raise IndexError(uid)
        async with self.messages_lock.read_lock():
            msg = self._messages.get(uid)
        if msg is None:
            if not isinstance(cached_msg, SQLiteMessage):
                raise TypeError(cached_msg)
            msg = SQLiteMessage.copy(cached_msg, expunged=True)
        return msg

    async def update(self, uid: int, cached_msg: CachedMessage,
                     flag_set: frozenset[Flag], mode: FlagOp) -> SQLiteMessage:
        msg = await self.get(uid, cached_msg)
        msg.permanent_flags = mode.apply(msg.permanent_flags, flag_set)
        db = await get_db()
        flag_str = ",".join(str(f) for f in msg.permanent_flags)
        await db.execute(
            "UPDATE messages SET flags = ? WHERE mailbox_id = ? AND uid = ?",
            (flag_str, self._mailbox_db_id, uid),
        )
        self._updated.set()
        return msg

    async def delete(self, uids: Iterable[int]) -> None:
        db = await get_db()
        storage = MessageStorage(get_settings().MAIL_STORAGE_PATH)
        async with self.messages_lock.write_lock():
            for uid in uids:
                if uid in self._messages:
                    del self._messages[uid]
                    await storage.delete(self._username, self._mailbox_name, uid)
                    await db.execute(
                        "DELETE FROM messages WHERE mailbox_id = ? AND uid = ?",
                        (self._mailbox_db_id, uid),
                    )
            self._updated.set()

    async def claim_recent(self, selected: SelectedMailbox) -> None:
        db = await get_db()
        async for msg in self.messages():
            if msg.recent:
                msg.recent = False
                selected.session_flags.add_recent(msg.uid)
                flag_str = ",".join(str(f) for f in msg.permanent_flags)
                await db.execute(
                    "UPDATE messages SET flags = ? WHERE mailbox_id = ? AND uid = ?",
                    (flag_str, self._mailbox_db_id, msg.uid),
                )
        self._updated.set()

    async def cleanup(self) -> None:
        pass

    async def messages(self) -> AsyncIterable[SQLiteMessage]:
        async with self.messages_lock.read_lock():
            for msg in self._messages.values():
                yield msg

    async def snapshot(self) -> MailboxSnapshot:
        exists = 0
        recent = 0
        unseen = 0
        first_unseen = None
        async for msg in self.messages():
            exists += 1
            if msg.recent:
                recent += 1
            if Seen not in msg.permanent_flags:
                unseen += 1
                if first_unseen is None:
                    first_unseen = exists
        return MailboxSnapshot(
            self.mailbox_id, self.readonly, self.uid_validity,
            self.permanent_flags, self.session_flags,
            exists, recent, unseen, first_unseen, self._uid_next,
        )


class SQLiteMailboxSet(MailboxSetInterface[SQLiteMailboxData]):
    def __init__(self, user_id: int, username: str) -> None:
        self._user_id = user_id
        self._username = username
        self._mailboxes: dict[str, SQLiteMailboxData] = {}
        self._set_lock = subsystem.get().new_rwlock()
        self._subscribed: dict[str, bool] = {}

    @property
    def delimiter(self) -> str:
        return "/"

    async def _load_mailboxes(self) -> None:
        db = await get_db()
        rows = await db.fetchall(
            "SELECT id, name, uidvalidity, uidnext FROM mailboxes WHERE user_id = ?",
            (self._user_id,),
        )
        self._mailboxes = {}
        for row in rows:
            mbx = SQLiteMailboxData(
                self._user_id, self._username, row["name"],
                row["id"], row["uidvalidity"], row["uidnext"],
            )
            self._mailboxes[row["name"]] = mbx
        if "INBOX" not in self._mailboxes:
            cursor = await db.execute(
                "INSERT INTO mailboxes (user_id, name, uidvalidity, uidnext) VALUES (?, ?, ?, ?)",
                (self._user_id, "INBOX", MailboxSnapshot.new_uid_validity(), 1),
            )
            mbx = SQLiteMailboxData(
                self._user_id, self._username, "INBOX",
                cursor.lastrowid, MailboxSnapshot.new_uid_validity(), 1,
            )
            self._mailboxes["INBOX"] = mbx

    async def set_subscribed(self, name: str, subscribed: bool) -> None:
        async with self._set_lock.write_lock():
            self._subscribed[name] = subscribed

    async def list_subscribed(self) -> ListTree:
        async with self._set_lock.read_lock():
            mailboxes = [name for name in self._mailboxes.keys()
                         if self._subscribed.get(name)]
        return ListTree(self.delimiter).update("INBOX", *mailboxes)

    async def list_mailboxes(self) -> ListTree:
        async with self._set_lock.read_lock():
            mailboxes = list(self._mailboxes.keys())
        return ListTree(self.delimiter).update("INBOX", *mailboxes)

    async def get_mailbox(self, name: str) -> SQLiteMailboxData:
        if name.upper() == "INBOX":
            name = "INBOX"
        async with self._set_lock.read_lock():
            if name not in self._mailboxes:
                await self._load_mailboxes()
            return self._mailboxes[name]

    async def add_mailbox(self, name: str) -> ObjectId:
        async with self._set_lock.read_lock():
            if name in self._mailboxes:
                raise ValueError(name)
        async with self._set_lock.write_lock():
            db = await get_db()
            cursor = await db.execute(
                "INSERT INTO mailboxes (user_id, name, uidvalidity, uidnext) VALUES (?, ?, ?, ?)",
                (self._user_id, name, MailboxSnapshot.new_uid_validity(), 1),
            )
            mbx = SQLiteMailboxData(
                self._user_id, self._username, name,
                cursor.lastrowid, MailboxSnapshot.new_uid_validity(), 1,
            )
            self._mailboxes[name] = mbx
            return mbx.mailbox_id

    async def delete_mailbox(self, name: str) -> None:
        async with self._set_lock.read_lock():
            if name not in self._mailboxes:
                raise KeyError(name)
        async with self._set_lock.write_lock():
            mbx = self._mailboxes.pop(name)
            db = await get_db()
            await db.execute("DELETE FROM mailboxes WHERE id = ?",
                             (mbx._mailbox_db_id,))

    async def rename_mailbox(self, before: str, after: str) -> None:
        async with self._set_lock.read_lock():
            if before not in self._mailboxes:
                raise KeyError(before)
            if after in self._mailboxes:
                raise ValueError(after)
        async with self._set_lock.write_lock():
            mbx = self._mailboxes.pop(before)
            self._mailboxes[after] = mbx
            mbx._mailbox_name = after
            db = await get_db()
            await db.execute("UPDATE mailboxes SET name = ? WHERE id = ?",
                             (after, mbx._mailbox_db_id))
