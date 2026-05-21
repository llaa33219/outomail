import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.auth import authenticate_user, create_api_key, create_user
from app.db import Database, get_db
from app.models import APIKeyResponse, AuthResponse, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Database = Depends(get_db)):
    try:
        user_id = await create_user(
            db, user_data.email, user_data.password, user_data.display_name
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")

    await db.execute(
        "INSERT INTO mailboxes (user_id, name, special_use) VALUES (?, ?, ?)",
        (user_id, "INBOX", "INBOX"),
    )

    user_row = await db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
    return UserResponse(**dict(user_row))


@router.post("/login", response_model=AuthResponse)
async def login(credentials: UserLogin, db: Database = Depends(get_db)):
    user = await authenticate_user(db, credentials.email, credentials.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    key = await create_api_key(db, user["id"], "Login")

    key_row = await db.fetchone("SELECT * FROM api_keys WHERE key = ?", (key,))
    api_key_response = APIKeyResponse(**dict(key_row))
    user_response = UserResponse(**user)

    return AuthResponse(api_key=api_key_response, user=user_response)
