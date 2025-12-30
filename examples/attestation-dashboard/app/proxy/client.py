"""HTTP client for proxying requests."""

import logging
from typing import Dict, Optional, Tuple

import httpx
from fastapi import Request, Response

logger = logging.getLogger(__name__)

# Headers to skip when forwarding
SKIP_REQUEST_HEADERS = {
    "host",
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

SKIP_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-encoding",  # Let FastAPI handle encoding
    "content-length",  # Let FastAPI calculate
}


def filter_request_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Filter headers to forward to upstream."""
    return {
        k: v
        for k, v in headers.items()
        if k.lower() not in SKIP_REQUEST_HEADERS
    }


def filter_response_headers(headers: httpx.Headers) -> Dict[str, str]:
    """Filter headers to return from upstream."""
    return {
        k: v
        for k, v in headers.items()
        if k.lower() not in SKIP_RESPONSE_HEADERS
    }


class ProxyClient:
    """Async HTTP client for proxying requests."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    async def forward_request(
        self,
        request: Request,
        target_url: str,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, str], bytes]:
        """
        Forward a request to the target URL.

        Args:
            request: The incoming FastAPI request
            target_url: URL to forward to
            extra_headers: Additional headers to include

        Returns:
            Tuple of (status_code, headers, content)
        """
        client = await self.get_client()

        # Build headers
        headers = filter_request_headers(dict(request.headers))
        if extra_headers:
            headers.update(extra_headers)

        # Get request body
        body = await request.body()

        # Forward the request
        logger.debug(f"Proxying {request.method} {target_url}")

        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params),
            )

            return (
                response.status_code,
                filter_response_headers(response.headers),
                response.content,
            )

        except httpx.TimeoutException:
            logger.error(f"Timeout proxying to {target_url}")
            raise
        except httpx.ConnectError as e:
            logger.error(f"Connection error proxying to {target_url}: {e}")
            raise

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global client instance
_proxy_client: Optional[ProxyClient] = None


def get_proxy_client(timeout: float = 30.0) -> ProxyClient:
    """Get or create the global proxy client."""
    global _proxy_client
    if _proxy_client is None:
        _proxy_client = ProxyClient(timeout=timeout)
    return _proxy_client
