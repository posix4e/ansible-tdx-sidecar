"""API routes package."""

from fastapi import APIRouter

from .health import router as health_router
from .registrations import router as registrations_router
from .verification import router as verification_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(registrations_router, prefix="/registrations", tags=["registrations"])
api_router.include_router(verification_router, prefix="/verify", tags=["verification"])
