"""Health check endpoints."""

import os
from datetime import datetime
from typing import Any, Dict

import httpx
from fastapi import APIRouter

from ...config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/")
async def root() -> Dict[str, Any]:
    """Dashboard information."""
    return {
        "name": settings.app_name,
        "description": "TDX Attestation Verification Dashboard and Proxy",
        "endpoints": {
            "/": "This page",
            "/health": "Health check",
            "/status": "TDX and system status",
            "/api/v1/registrations": "Manage registered applications",
            "/api/v1/verify": "Verification endpoints",
            "/proxy/{app_id}/{path}": "Attestation-verified proxy",
        },
    }


@router.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/status")
async def status() -> Dict[str, Any]:
    """System status including TDX availability."""
    result: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "app_name": settings.app_name,
        "tdx_proxy_url": settings.tdx_proxy_url,
        "database_url": settings.database_url.split("@")[-1] if "@" in settings.database_url else "sqlite",
    }

    # Check TDX proxy availability
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.tdx_proxy_url}/status",
                timeout=10.0,
            )
            result["tdx_status"] = response.json()
            result["tdx_available"] = True
    except Exception as e:
        result["tdx_status"] = {"error": str(e)}
        result["tdx_available"] = False

    # Check DCAP library availability
    result["dcap_library_available"] = os.path.exists(settings.dcap_library_path)

    return result
