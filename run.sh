#!/bin/bash
set -e

cd "$(dirname "$0")/outomail"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

check_port() {
    local port=$1
    if ss -tlnp | grep -q ":${port} "; then
        return 0
    else
        return 1
    fi
}

if [ ! -f .env ]; then
    echo -e "${BLUE}📧 outomail 설정을 시작합니다.${NC}"
    echo ""

    read -p "도메인 (예: example.com): " domain
    read -p "관리자 이메일 (예: admin@example.com): " admin_email
    read -s -p "관리자 비밀번호: " admin_password
    echo ""
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
LETSENCRYPT_ENABLED=true
LETSENCRYPT_EMAIL=${admin_email}
EOF

    echo -e "${GREEN}✅ .env 파일 생성 완료!${NC}"
    echo ""
fi

mkdir -p data/certs data/dkim data/mail

echo -e "${BLUE}🚀 outomail 시작...${NC}"
podman-compose up -d --build

echo ""
echo -e "${GREEN}✅ 컨테이너 시작 완료!${NC}"
echo ""

SERVER_IP=$(curl -s https://api.ipify.org)
DOMAIN=$(grep "^DOMAIN=" .env | cut -d'=' -f2)

echo -e "${YELLOW}🔥 방화벽 포트 확인 중...${NC}"
echo ""

PORTS=(25 587 993 7839)
PORT_NAMES=("SMTP" "SMTP Submission" "IMAP" "Web UI")
CLOSED_PORTS=()

for i in "${!PORTS[@]}"; do
    port=${PORTS[$i]}
    name=${PORT_NAMES[$i]}
    if check_port $port; then
        echo -e "  ${GREEN}✓${NC} 포트 $port ($name) - 열림"
    else
        echo -e "  ${RED}✗${NC} 포트 $port ($name) - 닫힘"
        CLOSED_PORTS+=($port)
    fi
done

if [ ${#CLOSED_PORTS[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}⚠️  일부 포트가 닫혀 있습니다!${NC}"
    echo ""
    echo "방화벽에서 아래 포트를 열어야 합니다:"
    echo ""
    echo -e "${BLUE}=== Hostinger VPS 방화벽 설정 ===${NC}"
    echo ""
    echo "1. Hostinger 대시보드 (hpanel.hostinger.com) 접속"
    echo "2. VPS → 관리 → 방화벽 설정"
    echo "3. Inbound 규칙 추가:"
    echo ""
    for port in "${CLOSED_PORTS[@]}"; do
        echo "   - 포트 $port / TCP / 허용"
    done
    echo ""
    echo -e "${BLUE}=== 또는 서버에서 직접 설정 ===${NC}"
    echo ""
    echo "sudo ufw allow 25/tcp"
    echo "sudo ufw allow 587/tcp"
    echo "sudo ufw allow 993/tcp"
    echo "sudo ufw allow 7839/tcp"
    echo "sudo ufw reload"
    echo ""
fi

echo -e "${YELLOW}🔒 TLS 인증서 확인 중...${NC}"
echo ""

sleep 5

if [ -f "data/certs/cert.pem" ] && [ -f "data/certs/key.pem" ]; then
    echo -e "${GREEN}✅ TLS 인증서 준비 완료!${NC}"
else
    echo -e "${YELLOW}⚠️  TLS 인증서를 확인하는 중입니다...${NC}"
fi

echo ""
echo -e "${BLUE}📋 DNS 설정이 필요합니다!${NC}"
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
echo "│ 4. DKIM 레코드 (TXT) - API로 확인 필요                                       "
echo "│    이름(Host): outomail._domainkey                                           "
echo "│    값(Value):  curl -H \"X-API-Key: KEY\" http://localhost:7839/api/settings/dns"
echo "│                                                                             "
echo "│ 5. DMARC 레코드 (TXT)                                                       "
echo "│    이름(Host): _dmarc                                                       "
echo "│    값(Value):  v=DMARC1; p=quarantine; rua=mailto:dmarc@${DOMAIN}           "
echo "└─────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo -e "${BLUE}🔗 접속 정보${NC}"
echo ""
echo "   Web UI:    https://${DOMAIN}:7839"
echo "   SMTP:      ${DOMAIN}:25"
echo "   Submission:${DOMAIN}:587"
echo "   IMAP:      ${DOMAIN}:993"
echo ""
echo -e "${BLUE}📝 유용한 명령어${NC}"
echo ""
echo "   로그 확인:     podman-compose logs -f"
echo "   서버 중지:     podman-compose down"
echo "   DNS 확인:      curl -H \"X-API-Key: KEY\" http://localhost:7839/api/settings/dns"
echo "   TLS 상태 확인: curl -H \"X-API-Key: KEY\" http://localhost:7839/api/settings/tls"
echo ""
