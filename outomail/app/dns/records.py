import urllib.request

class DNSManager:
    def __init__(self, domain: str, dkim_manager) -> None:
        self.domain = domain
        self.dkim_manager = dkim_manager

    def get_server_ip(self) -> str:
        try:
            return urllib.request.urlopen("https://api.ipify.org").read().decode()
        except Exception:
            return "서버_IP_확인_필요"

    def get_mx_record(self) -> dict:
        return {
            "type": "MX",
            "name": self.domain,
            "value": f"10 {self.domain}",
            "ttl": 3600,
            "description": "Mail exchange record - directs email to your server",
            "instructions": [
                f"1. DNS 관리자 페이지에서 {self.domain} 도메인의 MX 레코드를 추가하세요",
                f"2. 값: 10 {self.domain}",
                "3. 우선순위(Priority): 10",
                "4. TTL: 3600 (또는 1시간)",
            ],
        }

    def get_spf_record(self) -> dict:
        return {
            "type": "TXT",
            "name": self.domain,
            "value": f"v=spf1 mx a:{self.domain} ~all",
            "ttl": 3600,
            "description": "Sender Policy Framework - prevents email spoofing",
            "instructions": [
                f"1. DNS 관리자 페이지에서 {self.domain} 도메인의 TXT 레코드를 추가하세요",
                f"2. 값: v=spf1 mx a:{self.domain} ~all",
                "3. 이 설정으로 당신의 서버에서 보내는 이메일만 허용됩니다",
            ],
        }

    def get_dkim_record(self) -> dict:
        return {
            "type": "TXT",
            "name": f"{self.dkim_manager.selector}._domainkey.{self.domain}",
            "value": self.dkim_manager.get_dns_record(),
            "ttl": 3600,
            "description": "DomainKeys Identified Mail - email digital signature",
            "instructions": [
                f"1. DNS 관리자 페이지에서 {self.dkim_manager.selector}._domainkey.{self.domain} TXT 레코드를 추가하세요",
                f"2. 값: {self.dkim_manager.get_dns_record()}",
                "3. 이 레코드는 이메일 서명을 검증하는 데 사용됩니다",
            ],
        }

    def get_dmarc_record(self) -> dict:
        return {
            "type": "TXT",
            "name": f"_dmarc.{self.domain}",
            "value": f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{self.domain}",
            "ttl": 3600,
            "description": "Domain-based Message Authentication - email authentication policy",
            "instructions": [
                f"1. DNS 관리자 페이지에서 _dmarc.{self.domain} TXT 레코드를 추가하세요",
                f"2. 값: v=DMARC1; p=quarantine; rua=mailto:dmarc@{self.domain}",
                "3. SPF/DKIM 실패 시 이메일을 격리(quarantine) 처리합니다",
            ],
        }

    def get_all_records(self) -> list[dict]:
        return [
            self.get_mx_record(),
            self.get_spf_record(),
            self.get_dkim_record(),
            self.get_dmarc_record(),
        ]

    def get_setup_instructions(self) -> dict:
        server_ip = self.get_server_ip()
        return {
            "domain": self.domain,
            "server_ip": server_ip,
            "step1": {
                "title": "A 레코드 설정",
                "description": f"{self.domain}이 서버 IP를 가리키도록 A 레코드를 추가하세요",
                "record": {
                    "type": "A",
                    "name": self.domain,
                    "value": server_ip,
                    "ttl": 3600,
                },
            },
            "step2": {
                "title": "MX 레코드 설정",
                "description": "이메일 수신을 위해 MX 레코드를 추가하세요",
                "record": self.get_mx_record(),
            },
            "step3": {
                "title": "SPF 레코드 설정",
                "description": "이메일 스푸핑 방지를 위해 SPF 레코드를 추가하세요",
                "record": self.get_spf_record(),
            },
            "step4": {
                "title": "DKIM 레코드 설정",
                "description": "이메일 서명을 위해 DKIM 레코드를 추가하세요",
                "record": self.get_dkim_record(),
            },
            "step5": {
                "title": "DMARC 레코드 설정",
                "description": "이메일 인증 정책을 위해 DMARC 레코드를 추가하세요",
                "record": self.get_dmarc_record(),
            },
            "verification": {
                "title": "DNS 설정 확인",
                "commands": [
                    f"dig A {self.domain}",
                    f"dig MX {self.domain}",
                    f"dig TXT {self.domain}",
                    f"dig TXT {self.dkim_manager.selector}._domainkey.{self.domain}",
                    f"dig TXT _dmarc.{self.domain}",
                ],
            },
        }
