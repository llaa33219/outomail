import ssl
from pathlib import Path

from aiosmtpd.controller import Controller

from app.config import get_settings
from app.smtp.handler import MailHandler
from app.smtp.auth import SMTPAuthenticator


class SMTPServer:
    def __init__(self, host: str = "0.0.0.0", port: int | None = None, handler: MailHandler | None = None, authenticator: SMTPAuthenticator | None = None) -> None:
        settings = get_settings()
        self.host = host
        self.port = port or settings.SMTP_PORT
        self.handler = handler or MailHandler()
        self.authenticator = authenticator or SMTPAuthenticator()
        self._controller: Controller | None = None
        self._ssl_context: ssl.SSLContext | None = None

        cert_path = Path(settings.TLS_CERT_PATH)
        key_path = Path(settings.TLS_KEY_PATH)
        if cert_path.exists() and key_path.exists():
            self._ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self._ssl_context.load_cert_chain(str(cert_path), str(key_path))

    def start(self) -> None:
        kwargs = {"authenticator": self.authenticator}
        if self._ssl_context is not None:
            kwargs["ssl_context"] = self._ssl_context
        self._controller = Controller(
            self.handler,
            hostname=self.host,
            port=self.port,
            **kwargs,
        )
        self._controller.start()

    def stop(self) -> None:
        if self._controller is not None:
            self._controller.stop()
            self._controller = None
