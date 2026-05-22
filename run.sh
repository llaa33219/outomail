#!/bin/bash
set -e

cd "$(dirname "$0")/outomail"

if [ ! -f .env ]; then
    echo "📧 outomail 설정을 시작합니다."
    echo ""

    read -p "도메인 (예: mail.example.com): " domain
    read -p "관리자 이메일 (예: admin@example.com): " admin_email
    read -s -p "관리자 비밀번호: " admin_password
    echo ""

    cat > .env << EOF
DOMAIN=${domain}
SMTP_PORT=25
SMTP_SUBMISSION_PORT=587
IMAP_PORT=993
HTTP_PORT=7839
DATABASE_PATH=data/outomail.db
MAIL_STORAGE_PATH=data/mail
TLS_CERT_PATH=data/certs/cert.pem
TLS_KEY_PATH=data/certs/key.pem
DKIM_SELECTOR=outomail
DKIM_KEY_PATH=data/dkim/private.pem
ADMIN_EMAIL=${admin_email}
ADMIN_PASSWORD=${admin_password}
LETSENCRYPT_ENABLED=false
LETSENCRYPT_EMAIL=${admin_email}
EOF

    echo ""
    echo "✅ .env 파일 생성 완료!"
    echo ""
fi

mkdir -p data/certs data/dkim data/mail

echo "🚀 outomail 시작..."
podman-compose up -d --build

echo ""
echo "✅ 실행 완료!"
echo "   Web UI:    http://localhost:7839"
echo "   SMTP:      localhost:25"
echo "   Submission:localhost:587"
echo "   IMAP:      localhost:993"
echo ""
echo "로그 확인: podman-compose logs -f"
echo "중지:      podman-compose down"
