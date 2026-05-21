import asyncio
import smtplib
from email.utils import parseaddr

import dns.resolver

from app.dns.dkim import DKIMManager


class SMTPDelivery:
    def __init__(self, dkim_manager: DKIMManager) -> None:
        self.dkim_manager = dkim_manager

    async def resolve_mx(self, domain: str) -> list[str]:
        try:
            answers = dns.resolver.resolve(domain, "MX")
            records = sorted(
                [(r.preference, str(r.exchange).rstrip(".")) for r in answers],
                key=lambda x: x[0],
            )
            return [host for _, host in records]
        except Exception:
            return []

    async def send_to_mx(
        self, mx_host: str, from_addr: str, to_addr: str, raw_bytes: bytes
    ) -> bool:
        try:
            return await asyncio.to_thread(
                self._send_sync, mx_host, from_addr, to_addr, raw_bytes
            )
        except Exception:
            return False

    def _send_sync(
        self, mx_host: str, from_addr: str, to_addr: str, raw_bytes: bytes
    ) -> bool:
        with smtplib.SMTP(mx_host, 25, timeout=30) as server:
            server.ehlo_or_helo_if_needed()
            server.sendmail(from_addr, [to_addr], raw_bytes)
            return True

    async def deliver(self, raw_bytes: bytes, from_addr: str, to_addr: str) -> bool:
        _, addr = parseaddr(to_addr)
        if not addr or "@" not in addr:
            return False
        domain = addr.split("@", 1)[1]

        signed = await self.dkim_manager.sign_email(raw_bytes)

        mx_hosts = await self.resolve_mx(domain)
        if not mx_hosts:
            return False

        for mx_host in mx_hosts:
            success = await self.send_to_mx(mx_host, from_addr, to_addr, signed)
            if success:
                return True

        return False
