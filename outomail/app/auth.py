import secrets

import bcrypt
from fastapi import Header, HTTPException

from app.db import Database, get_db


async def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


async def generate_api_key() -> str:
    return secrets.token_hex(32)


async def create_user(db: Database, email: str, password: str, display_name: str) -> int:
    password_hash = await hash_password(password)
    cursor = await db.execute(
        "INSERT INTO users (email, password_hash, display_name) VALUES (?, ?, ?)",
        (email, password_hash, display_name),
    )
    return cursor.lastrowid


async def create_api_key(db: Database, user_id: int, name: str) -> str:
    key = await generate_api_key()
    await db.execute(
        "INSERT INTO api_keys (user_id, key, name) VALUES (?, ?, ?)",
        (user_id, key, name),
    )
    return key


async def authenticate_user(db: Database, email: str, password: str) -> dict | None:
    row = await db.fetchone("SELECT * FROM users WHERE email = ?", (email,))
    if row is None:
        return None
    user = dict(row)
    if not await verify_password(password, user["password_hash"]):
        return None
    return user


async def authenticate_api_key(db: Database, key: str) -> dict | None:
    row = await db.fetchone(
        "SELECT users.* FROM users JOIN api_keys ON users.id = api_keys.user_id WHERE api_keys.key = ?",
        (key,),
    )
    if row is None:
        return None
    await db.execute(
        "UPDATE api_keys SET last_used_at = strftime('%s', 'now') WHERE key = ?",
        (key,),
    )
    return dict(row)


async def get_current_user(
    x_api_key: str = Header(None),
    authorization: str = Header(None),
) -> dict:
    db = await get_db()
    if x_api_key:
        user = await authenticate_api_key(db, x_api_key)
        if user:
            return user
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        user = await authenticate_api_key(db, token)
        if user:
            return user
    raise HTTPException(status_code=401, detail="Unauthorized")
