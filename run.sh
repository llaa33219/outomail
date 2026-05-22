#!/bin/bash
set -e

cd "$(dirname "$0")/outomail"

if [ ! -f .env ]; then
    echo "📧 outomail 설정을 시작합니다."
    echo ""

    read -p "도메인 (예: example.com): " domain
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

SERVER_IP=$(curl -s https://api.ipify.org)
DOMAIN=$(grep "^DOMAIN=" .env | cut -d'=' -f2)

echo "📋 DNS 설정이 필요합니다!"
echo ""
echo "아래 레코드를 DNS 관리자 페이지에서 설정하세요:"
echo ""
echo "┌─────────────────────────────────────────────────────────────────────────────┐"
echo "│ 1. A 레코드                                                                 │"
echo "│    이름(Host): @                                                            "
echo "│    값(Value):  ${SERVER_IP}                                                 "
echo "│    TTL:        3600                                                         "
echo "│                                                                             "
echo "│ 2. MX 레코드                                                                "
echo "│    이름(Host):       @                                                      "
echo "│    값(Value):        ${DOMAIN}                                              "
echo "│    우선순위(Priority): 10                                                    "
echo "│    TTL:              3600                                                   "
echo "│                                                                             "
echo "│ 3. SPF 레코드 (TXT)                                                         "
echo "│    이름(Host): @                                                            "
echo "│    값(Value):  v=spf1 mx a:${DOMAIN} ~all                                   "
echo "│                                                                             "
echo "│ 4. DKIM 레코드 (TXT) - 서버 실행 후 확인 필요                                "
echo "│    이름(Host): outomail._domainkey                                           "
echo "│    값(Value):  API로 확인 필요                                               "
echo "│    명령어: curl -H \"X-API-Key: YOUR_KEY\" http://localhost:7839/api/settings/dns"
echo "│                                                                             "
echo "│ 5. DMARC 레코드 (TXT)                                                       "
echo "│    이름(Host): _dmarc                                                       "
echo "│    값(Value):  v=DMARC1; p=quarantine; rua=mailto:dmarc@${DOMAIN}           "
echo "└─────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "🔥 Hostinger VPS 방화벽 설정 (필수!)"
echo ""
echo "Hostinger VPS에서는 방화벽에서 포트를 열어야 합니다:"
echo ""
echo "  1. Hostinger 대시보드 → VPS → 방화벽 설정"
echo "  2. 아래 포트를 허용(Inbound) 규칙 추가:"
echo ""
echo "     포트 25   (SMTP)      - TCP"
echo "     포트 587  (Submission) - TCP"
echo "     포트 993  (IMAP)      - TCP"
echo "     포트 7839 (Web UI)    - TCP"
echo ""
echo "  또는 서버에서 iptables로 열기:"
echo ""
echo "     sudo iptables -A INPUT -p tcp --dport 25 -j ACCEPT"
echo "     sudo iptables -A INPUT -p tcp --dport 587 -j ACCEPT"
echo "     sudo iptables -A INPUT -p tcp --dport 993 -j ACCEPT"
echo "     sudo iptables -A INPUT -p tcp --dport 7839 -j ACCEPT"
echo "     sudo netfilter-persistent save"
echo ""
echo "DNS 설정 후 확인:"
echo "  dig A ${DOMAIN}"
echo "  dig MX ${DOMAIN} +short"
echo "  dig TXT ${DOMAIN}"
echo ""
echo "외부 접속 테스트:"
echo "  curl -v http://${DOMAIN}:7839/api/help"
echo ""
echo "로그 확인: podman-compose logs -f"
echo "중지:      podman-compose down"
