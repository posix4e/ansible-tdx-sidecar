"""Attestation-verified proxy router."""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings, get_settings
from ..core.attestation_cache import get_attestation_cache
from ..db import Registration, get_db
from .client import get_proxy_client
from .gate import attestation_gate, build_verification_headers

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_registration_by_id(
    app_id: str,
    db: AsyncSession,
) -> Registration:
    """Get registration or raise 404."""
    result = await db.execute(
        select(Registration).where(Registration.id == app_id)
    )
    registration = result.scalar_one_or_none()
    if not registration:
        raise HTTPException(status_code=404, detail=f"Application {app_id} not found")
    return registration


@router.get("/{app_id}/_status")
async def proxy_status(
    app_id: str,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """
    Get proxy status for a specific application.

    Returns attestation cache status and verification details.
    """
    registration = await get_registration_by_id(app_id, db)
    cache = get_attestation_cache(settings)

    # Get cached attestation if available
    cached = await cache.get(app_id)

    return {
        "app_id": app_id,
        "app_name": registration.name,
        "app_endpoint": registration.app_endpoint,
        "tdx_proxy_endpoint": registration.tdx_proxy_endpoint,
        "attestation_cached": cached is not None,
        "attestation_verified": cached.verified if cached else None,
        "attestation_cached_at": cached.cached_at.isoformat() if cached else None,
        "attestation_expires_at": cached.expires_at.isoformat() if cached else None,
        "dcap_status": cached.dcap.status if cached else None,
        "github_verified": cached.github.verified if cached else None,
        "measurements_verified": cached.measurements.verified if cached else None,
        "cache_stats": cache.stats(),
    }


@router.api_route(
    "/{app_id}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_request(
    app_id: str,
    path: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    """
    Attestation-verified proxy endpoint.

    Verifies the target application's TDX attestation before forwarding
    requests. Returns 403 if attestation fails.

    Headers added to response:
    - X-TDX-Verified: true/false
    - X-TDX-Verification-Time: ISO timestamp
    - X-TDX-DCAP-Status: DCAP verification status
    - X-TDX-Cache-Expires: When cached attestation expires
    """
    # Get registration
    registration = await get_registration_by_id(app_id, db)

    # Get cache
    cache = get_attestation_cache(settings)

    # Run attestation gate (raises HTTPException if fails)
    attestation = await attestation_gate(registration, cache, settings)

    # Build target URL
    target_url = f"{registration.app_endpoint}/{path}"
    if request.query_params:
        target_url += f"?{request.query_params}"

    # Get proxy client
    client = get_proxy_client(settings.proxy_request_timeout_seconds)

    try:
        # Forward request
        status_code, headers, content = await client.forward_request(
            request=request,
            target_url=f"{registration.app_endpoint}/{path}",
        )

        # Add verification headers
        verification_headers = build_verification_headers(attestation)
        headers.update(verification_headers)

        return Response(
            content=content,
            status_code=status_code,
            headers=headers,
        )

    except Exception as e:
        logger.exception(f"Proxy error for {app_id}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Proxy error",
                "message": str(e),
                "target": registration.app_endpoint,
            },
        )


@router.api_route("/{app_id}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_root(
    app_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    """Proxy requests to application root."""
    return await proxy_request(app_id, "", request, db, settings)
