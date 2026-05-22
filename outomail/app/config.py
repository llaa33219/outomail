from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DOMAIN: str
    SMTP_PORT: int = 25
    SMTP_SUBMISSION_PORT: int = 587
    IMAP_PORT: int = 993
    HTTP_PORT: int = 443
    DATABASE_PATH: str = "data/outomail.db"
    MAIL_STORAGE_PATH: str = "data/mail"
    TLS_CERT_PATH: str = "data/certs/cert.pem"
    TLS_KEY_PATH: str = "data/certs/key.pem"
    DKIM_SELECTOR: str = "outomail"
    DKIM_KEY_PATH: str = "data/dkim/private.pem"
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    LETSENCRYPT_ENABLED: bool = False
    LETSENCRYPT_EMAIL: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
