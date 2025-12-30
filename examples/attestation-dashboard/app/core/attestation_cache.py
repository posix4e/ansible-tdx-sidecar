"""Attestation result caching with TTL."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from ..api.schemas import (
    DCAPVerificationResult,
    GitHubVerificationResult,
    MeasurementVerificationResult,
)
from ..config import Settings
from ..db.models import Registration

logger = logging.getLogger(__name__)


@dataclass
class CachedAttestation:
    """Cached attestation verification result."""

    app_id: str
    verified: bool
    dcap: DCAPVerificationResult
    github: GitHubVerificationResult
    measurements: MeasurementVerificationResult
    cached_at: datetime
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        """Check if the cached result has expired."""
        return datetime.utcnow() > self.expires_at


@dataclass
class AttestationCache:
    """
    TTL-based cache for attestation verification results.

    Caches successful verifications to avoid repeated verification
    for every proxied request.
    """

    ttl_seconds: int = 300  # 5 minutes default
    _cache: Dict[str, CachedAttestation] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _pending: Dict[str, asyncio.Event] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize lock if not provided."""
        if self._lock is None:
            self._lock = asyncio.Lock()

    async def get(self, app_id: str) -> Optional[CachedAttestation]:
        """
        Get cached attestation if valid.

        Args:
            app_id: Application registration ID

        Returns:
            CachedAttestation if found and not expired, None otherwise
        """
        async with self._lock:
            cached = self._cache.get(app_id)
            if cached and not cached.is_expired:
                logger.debug(f"Cache hit for {app_id}")
                return cached
            elif cached:
                logger.debug(f"Cache expired for {app_id}")
                del self._cache[app_id]
            return None

    async def set(
        self,
        app_id: str,
        verified: bool,
        dcap: DCAPVerificationResult,
        github: GitHubVerificationResult,
        measurements: MeasurementVerificationResult,
    ) -> CachedAttestation:
        """
        Cache an attestation result.

        Args:
            app_id: Application registration ID
            verified: Overall verification result
            dcap: DCAP verification result
            github: GitHub verification result
            measurements: Measurement verification result

        Returns:
            The cached attestation
        """
        now = datetime.utcnow()
        cached = CachedAttestation(
            app_id=app_id,
            verified=verified,
            dcap=dcap,
            github=github,
            measurements=measurements,
            cached_at=now,
            expires_at=now + timedelta(seconds=self.ttl_seconds),
        )

        async with self._lock:
            self._cache[app_id] = cached
            logger.info(f"Cached attestation for {app_id}, expires at {cached.expires_at}")

        return cached

    async def invalidate(self, app_id: str) -> None:
        """
        Remove an attestation from cache.

        Args:
            app_id: Application registration ID
        """
        async with self._lock:
            if app_id in self._cache:
                del self._cache[app_id]
                logger.info(f"Invalidated cache for {app_id}")

    async def clear(self) -> None:
        """Clear all cached attestations."""
        async with self._lock:
            self._cache.clear()
            logger.info("Cleared attestation cache")

    async def get_or_verify(
        self,
        registration: Registration,
        settings: Settings,
    ) -> CachedAttestation:
        """
        Get cached attestation or perform verification.

        Uses a pending map to prevent duplicate verification for the same app.

        Args:
            registration: Application registration
            settings: Application settings

        Returns:
            CachedAttestation (from cache or freshly verified)
        """
        from .chain_verifier import ChainVerifier

        app_id = registration.id

        # Check cache first
        cached = await self.get(app_id)
        if cached:
            return cached

        # Check if verification is already in progress
        async with self._lock:
            if app_id in self._pending:
                event = self._pending[app_id]
            else:
                event = asyncio.Event()
                self._pending[app_id] = event

        # If we created the event, we do the verification
        if not event.is_set():
            try:
                logger.info(f"Starting verification for {app_id}")
                verifier = ChainVerifier(settings)

                result = await verifier.verify(registration)

                # Determine overall success
                verified = (
                    result.dcap.verified
                    and result.github.verified
                    and result.measurements.verified
                )

                # Cache the result
                cached = await self.set(
                    app_id=app_id,
                    verified=verified,
                    dcap=result.dcap,
                    github=result.github,
                    measurements=result.measurements,
                )

                return cached

            finally:
                # Signal completion
                async with self._lock:
                    if app_id in self._pending:
                        self._pending[app_id].set()
                        del self._pending[app_id]
        else:
            # Wait for in-progress verification
            await event.wait()
            # Try to get from cache again
            cached = await self.get(app_id)
            if cached:
                return cached
            # If still not in cache, something went wrong
            raise RuntimeError(f"Verification completed but no cache entry for {app_id}")

    def stats(self) -> Dict:
        """Get cache statistics."""
        now = datetime.utcnow()
        valid = sum(1 for c in self._cache.values() if not c.is_expired)
        expired = len(self._cache) - valid
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid,
            "expired_entries": expired,
            "ttl_seconds": self.ttl_seconds,
        }


# Global cache instance
_attestation_cache: Optional[AttestationCache] = None


def get_attestation_cache(settings: Settings) -> AttestationCache:
    """Get or create the global attestation cache."""
    global _attestation_cache
    if _attestation_cache is None:
        _attestation_cache = AttestationCache(ttl_seconds=settings.attestation_cache_ttl_seconds)
    return _attestation_cache
