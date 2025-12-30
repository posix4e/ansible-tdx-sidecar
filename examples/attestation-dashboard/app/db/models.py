"""SQLAlchemy ORM models for TDX attestation dashboard."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class VerificationStatus(str, Enum):
    """Status of a verification attempt."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


def generate_uuid():
    """Generate a new UUID."""
    return str(uuid.uuid4())


class Registration(Base):
    """Registered application for TDX attestation verification."""

    __tablename__ = "registrations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Container image details
    image_repository = Column(String(512), nullable=False)
    image_tag = Column(String(128), default="latest")
    image_digest = Column(String(128))

    # GitHub source details
    github_org = Column(String(255), nullable=False)
    github_repo = Column(String(255), nullable=False)
    github_workflow = Column(String(255), default=".github/workflows/build.yml")

    # Expected TDX measurements (48 bytes = 96 hex chars)
    expected_mrtd = Column(String(96))
    expected_rtmr0 = Column(String(96))
    expected_rtmr1 = Column(String(96))
    expected_rtmr2 = Column(String(96))
    expected_rtmr3 = Column(String(96))

    # Dockerfile reference
    dockerfile_path = Column(String(512), default="Dockerfile")
    dockerfile_sha256 = Column(String(64))

    # Proxy endpoints
    app_endpoint = Column(String(512), nullable=False)  # e.g., http://10.0.0.5:8080
    tdx_proxy_endpoint = Column(String(512), nullable=False)  # e.g., http://10.0.0.5:8081

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    verifications = relationship(
        "VerificationLog", back_populates="registration", cascade="all, delete-orphan"
    )


class VerificationLog(Base):
    """Log of verification attempts and results."""

    __tablename__ = "verification_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    registration_id = Column(
        String(36), ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False
    )

    # Overall status
    status = Column(
        SQLEnum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False
    )

    # DCAP verification results
    dcap_verified = Column(Boolean, default=False)
    dcap_status = Column(String(64))
    dcap_tcb_status = Column(String(64))
    dcap_collateral_expiry = Column(DateTime)

    # GitHub attestation results
    github_verified = Column(Boolean, default=False)
    github_signer_identity = Column(String(512))
    github_workflow_ref = Column(String(512))
    github_build_trigger = Column(String(64))

    # Measurement verification results
    measurements_verified = Column(Boolean, default=False)
    actual_mrtd = Column(String(96))
    actual_rtmr0 = Column(String(96))
    actual_rtmr1 = Column(String(96))
    actual_rtmr2 = Column(String(96))
    actual_rtmr3 = Column(String(96))

    # Raw data storage
    raw_quote = Column(Text)  # Base64 encoded TDX quote
    raw_attestation_bundle = Column(Text)  # JSON Sigstore bundle

    # Error details
    error_message = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    verification_duration_ms = Column(Integer)

    # Relationships
    registration = relationship("Registration", back_populates="verifications")
