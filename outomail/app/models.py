from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=100)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    is_active: bool
    created_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class APIKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class APIKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None


class MailboxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    special_use: Optional[str] = None
    uidnext: int = Field(ge=1)


class MessageCreate(BaseModel):
    to: EmailStr
    subject: str = Field(max_length=998)
    body: str
    cc: Optional[str] = None
    html: Optional[str] = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uid: int
    message_id: str
    subject: str
    from_addr: str
    to_addr: str
    date: datetime
    size: int = Field(ge=0)
    flags: List[str] = []
    has_attachments: bool = False


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    size: int = Field(ge=0)
    content_id: Optional[str] = None
    disposition: Optional[str] = None


class MessageDetail(MessageResponse):
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    headers: Dict[str, str] = {}
    attachments: List[AttachmentResponse] = []


class SearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    subject: str
    from_addr: str
    date: datetime
    snippet: str
    rank: float = Field(ge=0.0)


class DNSRecord(BaseModel):
    type: str
    name: str
    value: str
    ttl: int = Field(ge=0)
    description: Optional[str] = None


class DNSConfig(BaseModel):
    records: List[DNSRecord] = []
    domain: str


class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    api_key: APIKeyResponse
    user: UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
