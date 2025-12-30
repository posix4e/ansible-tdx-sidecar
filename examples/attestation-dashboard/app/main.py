#!/usr/bin/env python3
"""
TDX Attestation Dashboard & Verification Proxy

A FastAPI application that:
1. Manages registered TDX applications
2. Verifies DCAP attestations
3. Verifies GitHub Actions artifact attestations
4. Acts as an attestation-verified reverse proxy
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import api_router
from .config import get_settings
from .db import init_db
from .proxy import proxy_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if get_settings().debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting TDX Attestation Dashboard")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down TDX Attestation Dashboard")
    # Cleanup resources
    from .core.attestation_cache import _attestation_cache
    from .proxy.client import _proxy_client

    if _proxy_client:
        await _proxy_client.close()


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="TDX Attestation Verification Dashboard and Proxy",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api/v1")

# Proxy routes
app.include_router(proxy_router, prefix="/proxy", tags=["proxy"])

# Static files for frontend (if built)
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dist / "assets")), name="static")

    @app.get("/")
    async def serve_spa():
        """Serve the React SPA."""
        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa_routes(full_path: str):
        """Serve SPA for all non-API routes."""
        # Check if it's a static file
        static_file = frontend_dist / full_path
        if static_file.exists() and static_file.is_file():
            return FileResponse(str(static_file))
        # Otherwise serve the SPA
        return FileResponse(str(frontend_dist / "index.html"))
else:
    # Include health routes at root when no frontend
    from .api.routes.health import router as health_router
    app.include_router(health_router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
