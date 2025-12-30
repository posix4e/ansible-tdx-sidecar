"""Self-registration module for TDX applications."""

import logging
import os
import socket
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Configuration from environment
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "http://dashboard:8080")
APP_NAME = os.environ.get("APP_NAME", "sample-tdx-app")
APP_PORT = int(os.environ.get("APP_PORT", "8080"))
APP_HOST = os.environ.get("APP_HOST", "")  # If empty, will try to detect
GITHUB_ORG = os.environ.get("GITHUB_ORG", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
IMAGE_REPO = os.environ.get("IMAGE_REPO", "")
IMAGE_TAG = os.environ.get("IMAGE_TAG", "latest")
IMAGE_DIGEST = os.environ.get("IMAGE_DIGEST", "")
TDX_PROXY_PORT = int(os.environ.get("TDX_PROXY_PORT", "8081"))

# Registration settings
REGISTRATION_RETRIES = int(os.environ.get("REGISTRATION_RETRIES", "5"))
REGISTRATION_RETRY_DELAY = int(os.environ.get("REGISTRATION_RETRY_DELAY", "5"))
CAPTURE_BASELINE = os.environ.get("CAPTURE_BASELINE", "true").lower() == "true"


def get_host_ip() -> str:
    """Try to determine the host IP address."""
    if APP_HOST:
        return APP_HOST

    # Try to get the IP by connecting to an external address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        pass

    # Fallback to hostname
    return socket.gethostname()


def self_register() -> Optional[dict]:
    """
    Register this application with the attestation dashboard.

    Returns the registration response if successful, None otherwise.
    """
    host_ip = get_host_ip()
    logger.info(f"Detected host IP: {host_ip}")

    registration_data = {
        "name": APP_NAME,
        "description": f"Self-registered TDX application from {host_ip}",
        "github_org": GITHUB_ORG,
        "github_repo": GITHUB_REPO,
        "image_repository": IMAGE_REPO,
        "image_tag": IMAGE_TAG,
        "image_digest": IMAGE_DIGEST if IMAGE_DIGEST else None,
        "app_endpoint": f"http://{host_ip}:{APP_PORT}",
        "tdx_proxy_endpoint": f"http://{host_ip}:{TDX_PROXY_PORT}",
    }

    # Remove None values
    registration_data = {k: v for k, v in registration_data.items() if v}

    for attempt in range(1, REGISTRATION_RETRIES + 1):
        try:
            logger.info(f"Registration attempt {attempt}/{REGISTRATION_RETRIES}")

            with httpx.Client(timeout=30.0) as client:
                # Register with dashboard
                resp = client.post(
                    f"{DASHBOARD_URL}/api/v1/registrations",
                    json=registration_data,
                )
                resp.raise_for_status()
                registration = resp.json()
                logger.info(f"Registered successfully with ID: {registration['id']}")

                # Optionally capture baseline measurements
                if CAPTURE_BASELINE:
                    logger.info("Capturing baseline measurements...")
                    try:
                        baseline_resp = client.post(
                            f"{DASHBOARD_URL}/api/v1/verify/baseline",
                            json={"registration_id": registration["id"]},
                            timeout=60.0,
                        )
                        baseline_resp.raise_for_status()
                        baseline = baseline_resp.json()
                        logger.info(f"Baseline captured at {baseline.get('captured_at')}")
                    except Exception as e:
                        logger.warning(f"Failed to capture baseline: {e}")

                return registration

        except httpx.ConnectError as e:
            logger.warning(f"Connection error: {e}")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.warning(f"Registration error: {e}")

        if attempt < REGISTRATION_RETRIES:
            logger.info(f"Retrying in {REGISTRATION_RETRY_DELAY} seconds...")
            time.sleep(REGISTRATION_RETRY_DELAY)

    logger.error("Failed to register after all retries")
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = self_register()
    if result:
        print(f"Registration successful: {result}")
    else:
        print("Registration failed")
