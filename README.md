# outomail

Self-hosted mail server with REST API. Humans and bots treated equally.

## Features

- **SMTP** - Send and receive email (ports 25, 587)
- **IMAP** - Standard mail client support (port 993)
- **REST API** - Full control via curl at `/api`
- **Web GUI** - Simple mailbox interface at `/`
- **DKIM/SPF/DMARC** - Automatic DNS record generation
- **TLS** - Let's Encrypt integration
- **Full-text Search** - SQLite FTS5 powered

## Quick Start

```bash
# Clone and configure
git clone https://github.com/user/outomail.git
cd outomail
cp .env.example .env
# Edit .env with your domain

# Run with Podman
podman-compose up -d

# Check DNS records to configure
curl http://localhost:7839/api/settings/dns
```

## API Usage

```bash
# Register user
curl -X POST http://localhost:7839/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret"}'

# Login (get API key)
curl -X POST http://localhost:7839/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret"}'

# Send email
curl -X POST http://localhost:7839/api/messages \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"to": "recipient@example.com", "subject": "Hello", "body": "World"}'

# List mailboxes
curl http://localhost:7839/api/mailboxes \
  -H "X-API-Key: YOUR_API_KEY"

# Search emails
curl "http://localhost:7839/api/search?q=invoice" \
  -H "X-API-Key: YOUR_API_KEY"
```

## DNS Configuration

After running, check required DNS records:

```bash
curl http://localhost:7839/api/settings/dns
```

Returns MX, SPF, DKIM, and DMARC records to configure.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      outomail                                │
├─────────────────────────────────────────────────────────────┤
│   / (GUI)           /api (REST)        :25/:587 (SMTP)    │
│   └─ Vanilla JS     └─ FastAPI          └─ aiosmtpd        │
│                                                             │
│   :993 (IMAP)       SQLite + FTS5       Filesystem         │
│   └─ pymap          └─ Metadata         └─ Raw messages    │
└─────────────────────────────────────────────────────────────┘
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run with hot reload
uv run uvicorn app.main:app --reload
```

## License

MIT
