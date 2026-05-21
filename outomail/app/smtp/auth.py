import bcrypt

from app.db import Database
from app.config import get_settings


class SMTPAuthenticator:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path
        self._db: Database | None = None

    async def _get_db(self) -> Database:
        if self._db is None:
            if self._db_path:
                self._db = Database(self._db_path)
            else:
                self._db = Database(get_settings().DATABASE_PATH)
            await self._db.connect()
        return self._db

    async def __call__(self, mechanism: str, login: tuple) -> str | None:
        db = await self._get_db()

        if mechanism.upper() == "LOGIN":
            username, password = login
            username = username.decode()
            password = password.decode()
        elif mechanism.upper() == "PLAIN":
            if len(login) == 3:
                _, username, password = login
            else:
                return "535 Authentication failed"
            username = username.decode()
            password = password.decode()
        else:
            return "504 Unsupported authentication mechanism"

        row = await db.fetchone(
            "SELECT id, password_hash, is_active FROM users WHERE email = ?",
            (username,)
        )
        if row is None:
            row = await db.fetchone(
                "SELECT id, password_hash, is_active FROM users WHERE LOWER(email) = ?",
                (username.lower(),)
            )
        if row is None:
            return "535 Authentication failed"
        if not row["is_active"]:
            return "535 Account disabled"
        if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            return "535 Authentication failed"
        return None
