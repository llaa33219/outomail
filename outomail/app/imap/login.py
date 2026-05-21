from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Final

from pysasl.creds.server import ServerCredentials
from pymap.exceptions import InvalidAuth, UserNotFound, AuthorizationFailure
from pymap.interfaces.login import LoginInterface, IdentityInterface
from pymap.interfaces.token import TokensInterface
from pymap.token import AllTokens
from pymap.user import UserMetadata

from app.auth import verify_password
from app.db import get_db


class _TokenConfig:
    pass


class SQLiteLogin(LoginInterface):
    def __init__(self) -> None:
        self._tokens = AllTokens(_TokenConfig())

    @property
    def tokens(self) -> TokensInterface:
        return self._tokens

    async def authenticate(self, credentials: ServerCredentials):
        db = await get_db()
        row = await db.fetchone(
            "SELECT email, password_hash FROM users WHERE email = ? AND is_active = 1",
            (credentials.authcid,),
        )
        if row is None:
            await asyncio.sleep(0.3)
            raise InvalidAuth()
        if not await verify_password(credentials.secret, row["password_hash"]):
            raise InvalidAuth()
        return SQLiteIdentity(credentials.authcid, self)

    async def authorize(self, authenticated, authzid):
        if authenticated.name != authzid:
            raise AuthorizationFailure()
        return SQLiteIdentity(authzid, self)


class SQLiteIdentity(IdentityInterface):
    def __init__(self, name: str, login: SQLiteLogin) -> None:
        self._name = name
        self.login: Final = login
        self._roles: frozenset[str] = frozenset()

    @property
    def name(self) -> str:
        return self._name

    @property
    def roles(self) -> frozenset[str]:
        return self._roles

    @asynccontextmanager
    async def new_session(self):
        from app.imap.backend import SQLiteSession, _get_config
        from app.imap.mailbox import SQLiteMailboxSet

        db = await get_db()
        row = await db.fetchone(
            "SELECT id FROM users WHERE email = ? AND is_active = 1",
            (self._name,),
        )
        if row is None:
            raise UserNotFound(self._name)
        user_id = row["id"]
        config = _get_config()
        mailbox_set = SQLiteMailboxSet(user_id, self._name)
        await mailbox_set._load_mailboxes()
        yield SQLiteSession(self._name, config, mailbox_set)

    async def new_token(self, *, expiration=None):
        return None

    async def get(self):
        db = await get_db()
        row = await db.fetchone(
            "SELECT email, password_hash FROM users WHERE email = ? AND is_active = 1",
            (self._name,),
        )
        if row is None:
            raise UserNotFound(self._name)
        return UserMetadata(
            config=self.login._tokens.config,
            name=self._name,
            password=row["password_hash"],
        )

    async def set(self, metadata):
        return None

    async def delete(self):
        pass
