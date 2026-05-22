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

서버 실행 후 DNS 레코드를 설정해야 합니다:

```bash
# DNS 설정 가이드 확인
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:7839/api/settings/dns/setup

# DNS 레코드 목록 확인
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:7839/api/settings/dns
```

### 필수 DNS 레코드

| 레코드 | 이름 | 값 | 설명 |
|--------|------|-----|------|
| MX | `@` | `10 mail.yourdomain.com` | 이메일 수신 |
| TXT | `@` | `v=spf1 mx a:yourdomain.com ~all` | 이메일 스푸핑 방지 |
| TXT | `outomail._domainkey` | DKIM 공개키 | 이메일 서명 검증 |
| TXT | `_dmarc` | `v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com` | 인증 정책 |

### DNS 설정 확인

```bash
dig MX yourdomain.com
dig TXT yourdomain.com
dig TXT outomail._domainkey.yourdomain.com
dig TXT _dmarc.yourdomain.com
```

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

Apache License 2.0
