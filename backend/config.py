"""Centralized runtime configuration for DirectCredit.

Environment variables are intentionally read in one place so development,
staging, and production can use the same application code with different
settings. Never commit real secrets; use the deployment platform's secret
store in production.
"""
from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

# Local .env is useful for development only. Production should inject env vars.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "DirectCredit")
    environment: str = os.getenv("APP_ENV", "development")
    debug: bool = _bool("DEBUG", False)
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./directcredit.db")
    cors_origins: tuple[str, ...] = tuple(
        x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()
    )
    directcredit_secret: str = os.getenv("DIRECTCREDIT_SECRET", "")
    seed_demo_data: bool = _bool("SEED_DEMO_DATA", False)
    allow_demo_credential_claim: bool = _bool("ALLOW_DEMO_CREDENTIAL_CLAIM", False)
    access_token_hours: int = int(os.getenv("ACCESS_TOKEN_HOURS", "24"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "10"))

    def validate(self) -> None:
        if self.environment.lower() in {"production", "prod"}:
            if not self.directcredit_secret or self.directcredit_secret in {"change-this-in-render", "change-me"}:
                raise RuntimeError("DIRECTCREDIT_SECRET must be configured in production")
            if self.debug:
                raise RuntimeError("DEBUG must be false in production")
            if self.allow_demo_credential_claim:
                raise RuntimeError("ALLOW_DEMO_CREDENTIAL_CLAIM must be false in production")
            if self.seed_demo_data:
                raise RuntimeError("SEED_DEMO_DATA must be false in production")
            if "*" in self.cors_origins:
                raise RuntimeError("CORS_ORIGINS must not be '*' in production")


settings = Settings()
settings.validate()
