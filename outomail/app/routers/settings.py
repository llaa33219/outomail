from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.config import get_settings
from app.dns.dkim import DKIMManager
from app.dns.records import DNSManager
from app.models import DNSConfig, DNSRecord
from app.tls.certbot import TLSManager

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_dns_manager() -> DNSManager:
    settings = get_settings()
    dkim_manager = DKIMManager(
        domain=settings.DOMAIN,
        selector=settings.DKIM_SELECTOR,
        key_path=settings.DKIM_KEY_PATH,
    )
    return DNSManager(domain=settings.DOMAIN, dkim_manager=dkim_manager)


@router.get("/dns", response_model=DNSConfig)
async def get_dns_settings(user: dict = Depends(get_current_user)):
    settings = get_settings()
    dkim_manager = DKIMManager(
        domain=settings.DOMAIN,
        selector=settings.DKIM_SELECTOR,
        key_path=settings.DKIM_KEY_PATH,
    )
    if not dkim_manager.key_path.exists():
        await dkim_manager.generate_keys()
    dns_manager = DNSManager(domain=settings.DOMAIN, dkim_manager=dkim_manager)
    records = dns_manager.get_all_records()
    return DNSConfig(
        domain=settings.DOMAIN,
        records=[DNSRecord(**r) for r in records],
    )


@router.get("/dns/setup")
async def get_dns_setup_instructions(user: dict = Depends(get_current_user)):
    settings = get_settings()
    dkim_manager = DKIMManager(
        domain=settings.DOMAIN,
        selector=settings.DKIM_SELECTOR,
        key_path=settings.DKIM_KEY_PATH,
    )
    if not dkim_manager.key_path.exists():
        await dkim_manager.generate_keys()
    dns_manager = DNSManager(domain=settings.DOMAIN, dkim_manager=dkim_manager)
    return dns_manager.get_setup_instructions()


@router.get("/tls")
async def get_tls_settings(user: dict = Depends(get_current_user)):
    settings = get_settings()
    tls_manager = TLSManager(
        domain=settings.DOMAIN,
        cert_path=settings.TLS_CERT_PATH,
        key_path=settings.TLS_KEY_PATH,
        email=settings.LETSENCRYPT_EMAIL or settings.ADMIN_EMAIL,
    )
    status = await tls_manager.get_certificate_status()
    return status


@router.post("/tls/renew")
async def renew_tls_certificate(user: dict = Depends(get_current_user)):
    settings = get_settings()
    tls_manager = TLSManager(
        domain=settings.DOMAIN,
        cert_path=settings.TLS_CERT_PATH,
        key_path=settings.TLS_KEY_PATH,
        email=settings.LETSENCRYPT_EMAIL or settings.ADMIN_EMAIL,
    )
    success = await tls_manager.renew_certificate()
    return {"success": success}
