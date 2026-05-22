# outomail

Self-hosted mail server with REST API. Humans and bots treated equally.

## Features

- **SMTP** - Send and receive email (ports 25, 587)
- **IMAP** - Standard mail client support (port 993)
- **REST API** - Full control via curl at `/api`
- **Web GUI** - Simple mailbox interface at `/`
- **DKIM/SPF/DMARC** - Automatic DNS record generation
- **TLS** - Auto SSL certificate generation
- **Full-text Search** - SQLite FTS5 powered

## Quick Start

```bash
git clone https://github.com/llaa33219/outomail.git
cd outomail
./run.sh
```

실행하면 자동으로:
1. 도메인, 이메일, 비밀번호 입력 요청
2. `.env` 파일 생성
3. 컨테이너 빌드 및 시작
4. 방화벽 포트 확인
5. TLS 인증서 자동 생성
6. DNS 설정 가이드 표시

## 방화벽 설정

Hostinger VPS를 사용하는 경우, 아래 포트를 열어야 합니다:

### Hostinger hPanel에서 설정

1. hpanel.hostinger.com 접속
2. VPS → 관리 → 방화벽 설정
3. Inbound 규칙 추가:

| 포트 | 프로토콜 | 설명 |
|------|----------|------|
| 25 | TCP | SMTP (메일 수신) |
| 587 | TCP | SMTP Submission |
| 993 | TCP | IMAP |
| 7839 | TCP | Web UI |

### 서버에서 직접 설정

```bash
sudo ufw allow 25/tcp
sudo ufw allow 587/tcp
sudo ufw allow 993/tcp
sudo ufw allow 7839/tcp
sudo ufw reload
```

## DNS 설정

서버 실행 후 아래 DNS 레코드를 설정하세요:

| 레코드 | 이름(Host) | 값(Value) | 우선순위 |
|--------|------------|-----------|----------|
| A | @ | 서버_IP | - |
| MX | @ | yourdomain.com | 10 |
| TXT | @ | v=spf1 mx a:yourdomain.com ~all | - |
| TXT | outomail._domainkey | DKIM 공개키 (API로 확인) | - |
| TXT | _dmarc | v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com | - |

### DNS 설정 확인

```bash
dig A yourdomain.com
dig MX yourdomain.com +short
dig TXT yourdomain.com
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

# Check DNS settings
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:7839/api/settings/dns

# Check TLS status
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:7839/api/settings/tls
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
