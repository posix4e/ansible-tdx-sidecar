"""Pydantic schemas for verification endpoints."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field

from ...db.models import VerificationStatus


class TDXMeasurements(BaseModel):
    """TDX measurement registers."""

    mrtd: str = Field(..., description="Trust Domain measurement (48 bytes hex)")
    rtmr0: str = Field(..., description="Runtime measurement register 0")
    rtmr1: str = Field(..., description="Runtime measurement register 1")
    rtmr2: str = Field(..., description="Runtime measurement register 2")
    rtmr3: str = Field(..., description="Runtime measurement register 3")


class DCAPVerificationResult(BaseModel):
    """DCAP quote verification result."""

    verified: bool
    status: str  # OK, SIGNATURE_INVALID, REVOKED, TCB_OUT_OF_DATE, etc.
    tcb_status: Optional[str] = None
    collateral_expiry: Optional[datetime] = None
    error: Optional[str] = None


class GitHubVerificationResult(BaseModel):
    """GitHub attestation verification result."""

    verified: bool
    signer_identity: Optional[str] = None
    workflow_ref: Optional[str] = None
    build_trigger: Optional[str] = None
    repository: Optional[str] = None
    error: Optional[str] = None


class MeasurementVerificationResult(BaseModel):
    """TDX measurement verification result."""

    verified: bool
    mrtd_match: bool = False
    rtmr0_match: bool = False
    rtmr1_match: bool = False
    rtmr2_match: bool = False
    rtmr3_match: bool = False
    actual_measurements: Optional[TDXMeasurements] = None
    expected_measurements: Optional[TDXMeasurements] = None
    error: Optional[str] = None


class VerificationRequest(BaseModel):
    """Request to perform verification."""

    registration_id: str
    quote_base64: Optional[str] = Field(
        None, description="Base64-encoded TDX quote. If not provided, fetched from tdx_proxy_endpoint"
    )
    report_data: Optional[str] = Field(
        None, description="Optional report data for quote binding"
    )


class VerificationResponse(BaseModel):
    """Complete verification response."""

    id: str
    registration_id: str
    status: VerificationStatus
    dcap: DCAPVerificationResult
    github: GitHubVerificationResult
    measurements: MeasurementVerificationResult
    verification_duration_ms: int
    created_at: datetime
    error: Optional[str] = None

    model_config = {"from_attributes": True}


class BaselineRequest(BaseModel):
    """Request to capture baseline measurements."""

    registration_id: str


class BaselineResponse(BaseModel):
    """Response with captured baseline measurements."""

    registration_id: str
    measurements: TDXMeasurements
    captured_at: datetime
