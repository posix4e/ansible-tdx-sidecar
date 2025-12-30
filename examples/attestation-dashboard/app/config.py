"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "TDX Attestation Dashboard"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8080

    # Database
    database_url: str = "sqlite+aiosqlite:///./attestation.db"
    # For PostgreSQL: "postgresql+asyncpg://user:pass@host:5432/dbname"

    # TDX Attestation
    tdx_proxy_url: str = "http://host.docker.internal:8081"

    # DCAP Verification
    dcap_library_path: str = "/usr/lib/x86_64-linux-gnu/libsgx_dcap_quoteverify.so"
    pccs_url: str = "https://localhost:8081"

    # GitHub Attestation
    github_token: Optional[str] = None
    github_api_base: str = "https://api.github.com"

    # Attestation Cache
    attestation_cache_ttl_seconds: int = 300  # 5 minutes

    # Proxy
    proxy_request_timeout_seconds: int = 30


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
