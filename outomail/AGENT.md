# AGENT.md - outomail Development Guide

## Project Overview

outomail is a self-hosted mail server with REST API, written in Python. It provides SMTP, IMAP, and HTTP interfaces for sending and receiving email.

## Tech Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI + uvicorn
- **SMTP**: aiosmtpd
- **IMAP**: pymap
- **Database**: SQLite + FTS5
- **DKIM**: dkimpy
- **DNS Validation**: checkdmarc
- **Deployment**: Podman

## Project Structure

```
outomail/
├── app/
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # Pydantic Settings
│   ├── db.py                # SQLite + FTS5
│   ├── models.py            # Pydantic models
│   ├── auth.py              # Auth module
│   ├── routers/             # REST API endpoints
│   ├── smtp/                # SMTP server
│   ├── imap/                # IMAP server
│   ├── dns/                 # DKIM + DNS records
│   ├── tls/                 # TLS certificates
│   └── storage/             # Filesystem storage
├── static/                  # Web GUI
├── tests/                   # Test suite
└── migrations/              # SQL migrations
```

## Development Workflow

1. **TDD**: Write tests first, then implement
2. **Async**: Use async/await throughout
3. **Type Hints**: Full type annotations required
4. **Linting**: ruff check + ruff format

## Commands

```bash
# Install
uv sync

# Test
uv run pytest

# Lint
uv run ruff check .
uv run ruff format .

# Run
uv run uvicorn app.main:app --reload

# Build container
podman build -t outomail .
```

## Key Patterns

- **Auth**: API keys (X-API-Key header) or passwords (bcrypt)
- **Database**: aiosqlite with WAL mode
- **Storage**: SQLite metadata + filesystem .eml files
- **SMTP**: aiosmtpd handlers for receive, dns.resolver for MX lookup
- **IMAP**: pymap backend subclass reading from filesystem

## Ports

| Port | Service | Protocol |
|------|---------|----------|
| 25 | SMTP | MX receive |
| 587 | SMTP Submission | Authenticated send |
| 993 | IMAPS | TLS |
| 443 | HTTP | API + GUI |
