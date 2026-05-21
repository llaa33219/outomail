import asyncio
import datetime
import os
import subprocess

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


class TLSManager:
    def __init__(self, domain: str, cert_path: str, key_path: str, email: str):
        self.domain = domain
        self.cert_path = cert_path
        self.key_path = key_path
        self.email = email

    async def get_certificate_status(self) -> dict:
        return await asyncio.to_thread(self._get_certificate_status_sync)

    def _get_certificate_status_sync(self) -> dict:
        status = {
            "exists": False,
            "valid": False,
            "expired": True,
            "expiry_date": None,
            "days_until_expiry": None,
            "domain_match": False,
            "error": None,
        }

        if not os.path.exists(self.cert_path):
            return status

        status["exists"] = True

        try:
            with open(self.cert_path, "rb") as f:
                cert_data = f.read()

            cert = x509.load_pem_x509_certificate(cert_data)
            now = datetime.datetime.now(datetime.timezone.utc)
            expiry = cert.not_valid_after_utc
            status["expiry_date"] = expiry.isoformat()
            status["days_until_expiry"] = (expiry - now).days
            status["expired"] = now > expiry

            if not status["expired"] and now >= cert.not_valid_before_utc:
                status["valid"] = True

            for attr in cert.subject:
                if attr.oid == NameOID.COMMON_NAME:
                    if attr.value == self.domain:
                        status["domain_match"] = True

            for ext in cert.extensions:
                if ext.oid == x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME:
                    san = ext.value
                    if self.domain in san.get_values_for_type(x509.DNSName):
                        status["domain_match"] = True

        except Exception as e:
            status["error"] = str(e)

        return status

    async def request_certificate(self) -> bool:
        return await asyncio.to_thread(self._request_certificate_sync)

    def _request_certificate_sync(self) -> bool:
        os.makedirs(os.path.dirname(self.cert_path), exist_ok=True)

        cmd = [
            "certbot",
            "certonly",
            "--standalone",
            "-d",
            self.domain,
            "--email",
            self.email,
            "--agree-tos",
            "--non-interactive",
            "--cert-path",
            self.cert_path,
            "--key-path",
            self.key_path,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.returncode == 0
        except Exception:
            return False

    async def renew_certificate(self) -> bool:
        return await asyncio.to_thread(self._renew_certificate_sync)

    def _renew_certificate_sync(self) -> bool:
        cmd = [
            "certbot",
            "renew",
            "--non-interactive",
            "--quiet",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.returncode == 0
        except Exception:
            return False

    async def generate_self_signed(self) -> tuple[str, str]:
        return await asyncio.to_thread(self._generate_self_signed_sync)

    def _generate_self_signed_sync(self) -> tuple[str, str]:
        os.makedirs(os.path.dirname(self.cert_path), exist_ok=True)

        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, self.domain),
        ])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=365)
            )
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(self.domain),
                ]),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )

        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        key_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        with open(self.cert_path, "wb") as f:
            f.write(cert_pem)

        with open(self.key_path, "wb") as f:
            f.write(key_pem)

        return self.cert_path, self.key_path

    async def ensure_certificate(self) -> tuple[str, str]:
        status = await self.get_certificate_status()

        if status["exists"] and status["valid"] and not status["expired"]:
            return self.cert_path, self.key_path

        if status["exists"] and status["expired"]:
            renewed = await self.renew_certificate()
            if renewed:
                return self.cert_path, self.key_path

        requested = await self.request_certificate()
        if requested:
            return self.cert_path, self.key_path

        return await self.generate_self_signed()
