import asyncio
from pathlib import Path


class MessageStorage:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def get_path(self, username: str, mailbox: str, uid: int) -> str:
        return str(self.base_path / username / mailbox / f"{uid}.eml")

    async def save(self, username: str, mailbox: str, uid: int, raw_bytes: bytes) -> str:
        path = self.base_path / username / mailbox / f"{uid}.eml"
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, raw_bytes)
        return str(path)

    async def read(self, username: str, mailbox: str, uid: int) -> bytes | None:
        path = self.base_path / username / mailbox / f"{uid}.eml"
        if not path.exists():
            return None
        return await asyncio.to_thread(path.read_bytes)

    async def delete(self, username: str, mailbox: str, uid: int) -> bool:
        path = self.base_path / username / mailbox / f"{uid}.eml"
        if not path.exists():
            return False
        await asyncio.to_thread(path.unlink)
        return True

    async def list_messages(self, username: str, mailbox: str) -> list[int]:
        path = self.base_path / username / mailbox
        if not path.exists():
            return []
        entries = await asyncio.to_thread(lambda: list(path.iterdir()))
        uids = []
        for entry in entries:
            if entry.is_file() and entry.suffix == ".eml":
                try:
                    uids.append(int(entry.stem))
                except ValueError:
                    continue
        return sorted(uids)
