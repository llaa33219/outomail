from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth import hash_password
from app.config import get_settings
from app.db import get_db, close_db
from app.dns.dkim import DKIMManager
from app.imap.server import IMAPServer
from app.routers import auth, mailboxes, messages, settings
from app.smtp.server import SMTPServer
from app.tls.certbot import TLSManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings_obj = get_settings()

    db = await get_db(settings_obj.DATABASE_PATH)

    admin = await db.fetchone(
        "SELECT * FROM users WHERE email = ?", (settings_obj.ADMIN_EMAIL,)
    )
    if admin is None:
        password_hash = await hash_password(settings_obj.ADMIN_PASSWORD)
        await db.execute(
            "INSERT INTO users (email, password_hash, display_name) VALUES (?, ?, ?)",
            (settings_obj.ADMIN_EMAIL, password_hash, "Admin"),
        )

    dkim_manager = DKIMManager(
        domain=settings_obj.DOMAIN,
        selector=settings_obj.DKIM_SELECTOR,
        key_path=settings_obj.DKIM_KEY_PATH,
    )
    if not dkim_manager.key_path.exists():
        await dkim_manager.generate_keys()

    tls_manager = TLSManager(
        domain=settings_obj.DOMAIN,
        cert_path=settings_obj.TLS_CERT_PATH,
        key_path=settings_obj.TLS_KEY_PATH,
        email=settings_obj.LETSENCRYPT_EMAIL or settings_obj.ADMIN_EMAIL,
    )
    await tls_manager.ensure_certificate()

    smtp_server = SMTPServer(port=settings_obj.SMTP_PORT)
    smtp_server.start()

    smtp_submission = SMTPServer(port=settings_obj.SMTP_SUBMISSION_PORT)
    smtp_submission.start()

    imap_server = IMAPServer(port=settings_obj.IMAP_PORT)
    await imap_server.start()

    yield

    smtp_server.stop()
    smtp_submission.stop()
    await imap_server.stop()
    await close_db()


app = FastAPI(title="outomail", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(mailboxes.router)
app.include_router(messages.router)
app.include_router(settings.router)


@app.get("/api/help")
async def api_help():
    routes = []
    for route in app.routes:
        if hasattr(route, "methods"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name,
                "summary": route.summary or "",
            })
    return {"routes": routes}


app.mount("/", StaticFiles(directory="static", html=True), name="static")


def cli():
    settings_obj = get_settings()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings_obj.HTTP_PORT,
        ssl_keyfile=settings_obj.TLS_KEY_PATH,
        ssl_certfile=settings_obj.TLS_CERT_PATH,
    )
