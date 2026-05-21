from __future__ import annotations

from argparse import Namespace
from contextlib import AsyncExitStack
from pathlib import Path

from pymap.backend.session import BaseSession
from pymap.config import IMAPConfig, BackendCapability
from pymap.health import HealthStatus
from pymap.interfaces.backend import BackendInterface
from pymap.interfaces.login import LoginInterface

from app.config import get_settings
from app.imap.login import SQLiteLogin
from app.imap.mailbox import SQLiteMailboxSet, SQLiteMessage


class SQLiteConfig(IMAPConfig):
    @property
    def backend_capability(self) -> BackendCapability:
        return BackendCapability(idle=True, object_id=True, multi_append=True)


class SQLiteSession(BaseSession[SQLiteMessage]):
    def __init__(self, owner: str, config: SQLiteConfig,
                 mailbox_set: SQLiteMailboxSet) -> None:
        super().__init__(owner)
        self._config = config
        self._mailbox_set = mailbox_set

    @property
    def config(self) -> SQLiteConfig:
        return self._config

    @property
    def mailbox_set(self) -> SQLiteMailboxSet:
        return self._mailbox_set


class SQLiteBackend(BackendInterface):
    def __init__(self, login: SQLiteLogin, config: SQLiteConfig) -> None:
        self._login = login
        self._config = config
        self._status = HealthStatus()

    @property
    def login(self) -> LoginInterface:
        return self._login

    @property
    def config(self) -> SQLiteConfig:
        return self._config

    @property
    def status(self) -> HealthStatus:
        return self._status

    @classmethod
    def add_subparser(cls, name, subparsers):
        pass

    @classmethod
    async def init(cls, args, **overrides):
        config = SQLiteConfig.from_args(args, **overrides)
        login = SQLiteLogin()
        return cls(login, config), config

    async def start(self, stack):
        pass

    def new_login(self):
        return SQLiteLogin()


def _get_config() -> SQLiteConfig:
    settings = get_settings()
    cert_file = settings.TLS_CERT_PATH
    key_file = settings.TLS_KEY_PATH
    cert_exists = Path(cert_file).exists() if cert_file else False
    key_exists = Path(key_file).exists() if key_file else False
    args = Namespace(
        host="0.0.0.0",
        port=settings.IMAP_PORT,
        debug=False,
        cert=cert_file,
        key=key_file,
        tls=False,
        inherited_sockets=None,
        proxy_protocol=None,
        passlib_cfg=None,
    )
    return SQLiteConfig(
        args,
        host="0.0.0.0",
        port=settings.IMAP_PORT,
        tls_enabled=False,
        cert_file=cert_file if cert_exists else None,
        key_file=key_file if key_exists else None,
    )
