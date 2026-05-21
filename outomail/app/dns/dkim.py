import asyncio
from pathlib import Path

import dkim
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class DKIMManager:
    def __init__(self, domain: str, selector: str, key_path: str) -> None:
        self.domain = domain
        self.selector = selector
        self.key_path = Path(key_path)
        self.public_key_path = self.key_path.with_suffix(".pub.pem")

    def _generate_keys_sync(self) -> tuple[str, str]:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        self.key_path.write_text(private_pem)
        self.public_key_path.write_text(public_pem)
        return private_pem, public_pem

    async def generate_keys(self) -> tuple[str, str]:
        return await asyncio.to_thread(self._generate_keys_sync)

    def load_private_key(self) -> bytes:
        return self.key_path.read_bytes()

    def load_public_key(self) -> bytes:
        return self.public_key_path.read_bytes()

    def get_dns_record(self) -> str:
        public_pem = self.load_public_key().decode("utf-8")
        lines = [
            line
            for line in public_pem.strip().splitlines()
            if not line.startswith("-----")
        ]
        b64_key = "".join(lines)
        return f"v=DKIM1; k=rsa; p={b64_key}"

    def _sign_email_sync(self, raw_bytes: bytes) -> bytes:
        private_key = self.load_private_key()
        sig = dkim.sign(
            raw_bytes,
            selector=self.selector.encode("utf-8"),
            domain=self.domain.encode("utf-8"),
            privkey=private_key,
        )
        return sig + raw_bytes

    async def sign_email(self, raw_bytes: bytes) -> bytes:
        return await asyncio.to_thread(self._sign_email_sync, raw_bytes)
