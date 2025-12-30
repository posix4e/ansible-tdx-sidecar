"""API schemas package."""

from .registration import (
    RegistrationCreate,
    RegistrationResponse,
    RegistrationUpdate,
)
from .verification import (
    DCAPVerificationResult,
    GitHubVerificationResult,
    MeasurementVerificationResult,
    TDXMeasurements,
    VerificationRequest,
    VerificationResponse,
)

__all__ = [
    "RegistrationCreate",
    "RegistrationResponse",
    "RegistrationUpdate",
    "DCAPVerificationResult",
    "GitHubVerificationResult",
    "MeasurementVerificationResult",
    "TDXMeasurements",
    "VerificationRequest",
    "VerificationResponse",
]
