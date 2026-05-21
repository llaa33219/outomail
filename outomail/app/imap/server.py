from __future__ import annotations

import asyncio
import ssl
from contextlib import AsyncExitStack
from pathlib import Path

from proxyprotocol.reader import ProxyProtocolReader
from pymap.imap import IMAPServer as _IMAPServer

from app.config import get_settings
from app.imap.backend import SQLiteBackend, SQLiteLogin, SQLiteConfig


class IMAPServer:
    def __init__(self, host: str = "0.0.0.0", port: int | None = None) -> None:
        settings = get_settings()
        self.host = host
        self.port = port or settings.IMAP_PORT
        self._server = None
        self._task = None
        self._stack = None

        cert_path = Path(settings.TLS_CERT_PATH)
        key_path = Path(settings.TLS_KEY_PATH)
        self._ssl_context = None
        if cert_path.exists() and key_path.exists():
            self._ssl_context = ssl.create_default_context(
                ssl.Purpose.CLIENT_AUTH
            )
            self._ssl_context.load_cert_chain(
                str(cert_path), str(key_path)
            )

    async def start(self) -> None:
        settings = get_settings()
        cert_file = settings.TLS_CERT_PATH
        key_file = settings.TLS_KEY_PATH
        cert_exists = Path(cert_file).exists() if cert_file else False
        key_exists = Path(key_file).exists() if key_file else False
        args = type(
            "Args",
            (),
            {
                "host": self.host,
                "port": self.port,
                "debug": False,
                "cert": cert_file,
                "key": key_file,
                "tls": False,
                "inherited_sockets": None,
                "proxy_protocol": None,
                "passlib_cfg": None,
            },
        )()
        config = SQLiteConfig(
            args,
            host=self.host,
            port=self.port,
            tls_enabled=False,
            cert_file=cert_file if cert_exists else None,
            key_file=key_file if key_exists else None,
        )
        backend = SQLiteBackend(SQLiteLogin(), config)
        await backend.start(AsyncExitStack())

        imap_server = _IMAPServer(backend.login, config)
        pp_reader = ProxyProtocolReader(config.proxy_protocol)
        callback = pp_reader.get_callback(imap_server)

        self._server = await asyncio.start_server(
            callback,
            host=self.host,
            port=self.port,
            ssl=self._ssl_context,
        )
        self._stack = AsyncExitStack()
        await self._stack.enter_async_context(self._server)
        self._task = asyncio.create_task(self._server.serve_forever())
        self._stack.callback(self._task.cancel)

    async def stop(self) -> None:
        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
