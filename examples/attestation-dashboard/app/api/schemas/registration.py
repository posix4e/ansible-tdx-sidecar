"""Pydantic schemas for registration endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RegistrationCreate(BaseModel):
    """Schema for creating a new registration."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    image_repository: str = Field(
        ..., description="Container registry path, e.g., ghcr.io/org/repo"
    )
    image_tag: Optional[str] = Field(default="latest")
    image_digest: Optional[str] = Field(
        None, pattern=r"^sha256:[a-f0-9]{64}$", description="Container image digest"
    )

    github_org: str = Field(..., description="GitHub organization or username")
    github_repo: str = Field(..., description="GitHub repository name")
    github_workflow: Optional[str] = Field(default=".github/workflows/build.yml")

    dockerfile_path: str = Field(default="Dockerfile")

    # Proxy endpoints
    app_endpoint: str = Field(
        ..., description="URL to proxy requests to, e.g., http://10.0.0.5:8080"
    )
    tdx_proxy_endpoint: str = Field(
        ..., description="URL to fetch TDX quotes from, e.g., http://10.0.0.5:8081"
    )

    # Optional: Pre-computed expected measurements (48 bytes = 96 hex chars)
    expected_mrtd: Optional[str] = Field(None, pattern=r"^[a-f0-9]{96}$")
    expected_rtmr0: Optional[str] = Field(None, pattern=r"^[a-f0-9]{96}$")
    expected_rtmr1: Optional[str] = Field(None, pattern=r"^[a-f0-9]{96}$")
    expected_rtmr2: Optional[str] = Field(None, pattern=r"^[a-f0-9]{96}$")
    expected_rtmr3: Optional[str] = Field(None, pattern=r"^[a-f0-9]{96}$")

    @field_validator("app_endpoint", "tdx_proxy_endpoint")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v.rstrip("/")


class RegistrationUpdate(BaseModel):
    """Schema for updating a registration."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    image_tag: Optional[str] = None
    image_digest: Optional[str] = Field(None, pattern=r"^sha256:[a-f0-9]{64}$")
    github_workflow: Optional[str] = None
    app_endpoint: Optional[str] = None
    tdx_proxy_endpoint: Optional[str] = None
    expected_mrtd: Optional[str] = Field(None, pattern=r"^[a-f0-9]{96}$")
    expected_rtmr0: Optional[str] = Field(None, pattern=r"^[a-f0-9]{96}$")
    expected_rtmr1: Optional[str] = Field(None, pattern=r"^[a-f0-9]{96}$")
    expected_rtmr2: Optional[str] = Field(None, pattern=r"^[a-f0-9]{96}$")
    expected_rtmr3: Optional[str] = Field(None, pattern=r"^[a-f0-9]{96}$")


class RegistrationResponse(BaseModel):
    """Schema for registration response."""

    id: str
    name: str
    description: Optional[str]
    image_repository: str
    image_tag: Optional[str]
    image_digest: Optional[str]
    github_org: str
    github_repo: str
    github_workflow: Optional[str]
    dockerfile_path: str
    app_endpoint: str
    tdx_proxy_endpoint: str
    expected_mrtd: Optional[str]
    expected_rtmr0: Optional[str]
    expected_rtmr1: Optional[str]
    expected_rtmr2: Optional[str]
    expected_rtmr3: Optional[str]
    created_at: datetime
    updated_at: datetime
    proxy_url: Optional[str] = None  # Computed field for proxy access URL

    model_config = {"from_attributes": True}
