"""Attestation gate middleware."""

import logging
from typing import Dict, Any

from fastapi import HTTPException

from ..config import Settings
from ..core.attestation_cache import AttestationCache, CachedAttestation
from ..db.models import Registration

logger = logging.getLogger(__name__)


async def attestation_gate(
    registration: Registration,
    cache: AttestationCache,
    settings: Settings,
) -> CachedAttestation:
    """
    Gate that blocks requests if attestation is invalid.

    Args:
        registration: The application registration
        cache: Attestation cache instance
        settings: Application settings

    Returns:
        CachedAttestation if verification passes

    Raises:
        HTTPException: If attestation verification fails
    """
    try:
        attestation = await cache.get_or_verify(registration, settings)
    except Exception as e:
        logger.exception(f"Attestation verification failed for {registration.id}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Attestation verification error",
                "message": str(e),
            },
        )

    if not attestation.verified:
        logger.warning(f"Attestation failed for {registration.id}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Attestation verification failed",
                "dcap_valid": attestation.dcap.verified,
                "dcap_status": attestation.dcap.status,
                "github_valid": attestation.github.verified,
                "github_error": attestation.github.error,
                "measurements_valid": attestation.measurements.verified,
                "measurements_error": attestation.measurements.error,
                "cached_at": attestation.cached_at.isoformat(),
            },
        )

    return attestation


def build_verification_headers(attestation: CachedAttestation) -> Dict[str, str]:
    """
    Build response headers indicating attestation status.

    Args:
        attestation: The cached attestation result

    Returns:
        Dictionary of headers to add to the response
    """
    return {
        "X-TDX-Verified": "true" if attestation.verified else "false",
        "X-TDX-Verification-Time": attestation.cached_at.isoformat(),
        "X-TDX-DCAP-Status": attestation.dcap.status,
        "X-TDX-Cache-Expires": attestation.expires_at.isoformat(),
    }
