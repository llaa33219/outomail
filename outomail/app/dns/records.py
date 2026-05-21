class DNSManager:
    def __init__(self, domain: str, dkim_manager) -> None:
        self.domain = domain
        self.dkim_manager = dkim_manager

    def get_mx_record(self) -> dict:
        return {
            "type": "MX",
            "name": self.domain,
            "value": f"10 mail.{self.domain}",
            "ttl": 3600,
            "description": "Mail exchange record",
        }

    def get_spf_record(self) -> dict:
        return {
            "type": "TXT",
            "name": self.domain,
            "value": f"v=spf1 mx a:{self.domain} ~all",
            "ttl": 3600,
            "description": "Sender Policy Framework record",
        }

    def get_dkim_record(self) -> dict:
        return {
            "type": "TXT",
            "name": f"{self.dkim_manager.selector}._domainkey.{self.domain}",
            "value": self.dkim_manager.get_dns_record(),
            "ttl": 3600,
            "description": "DomainKeys Identified Mail record",
        }

    def get_dmarc_record(self) -> dict:
        return {
            "type": "TXT",
            "name": f"_dmarc.{self.domain}",
            "value": f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{self.domain}",
            "ttl": 3600,
            "description": "Domain-based Message Authentication record",
        }

    def get_all_records(self) -> list[dict]:
        return [
            self.get_mx_record(),
            self.get_spf_record(),
            self.get_dkim_record(),
            self.get_dmarc_record(),
        ]
