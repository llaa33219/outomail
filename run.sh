#!/bin/bash
set -e

cd "$(dirname "$0")/outomail"

if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  .env 파일을 수정하세요 (DOMAIN, ADMIN_EMAIL, ADMIN_PASSWORD 등)"
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
