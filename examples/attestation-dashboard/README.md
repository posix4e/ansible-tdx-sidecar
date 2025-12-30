# TDX Attestation Dashboard & Verification Proxy

A web application for managing and verifying TDX-attested applications with an attestation-verified reverse proxy.

## Features

- **Application Registry**: Register TDX applications with their GitHub and container image info
- **DCAP Verification**: Verify TDX quotes using Intel's DCAP infrastructure
- **GitHub Attestation**: Verify container images were built by GitHub Actions (SLSA provenance)
- **Measurement Verification**: Compare TDX measurements against expected baselines
- **Attestation Proxy**: Reverse proxy that only forwards traffic to verified applications

## Architecture

```
┌──────────┐     ┌─────────────────────────┐     ┌─────────────────┐
│  Client  │────▶│   Attestation Proxy     │────▶│  TDX App (VM)   │
└──────────┘     │  1. Check registration  │     │  - App on :8080 │
                 │  2. Verify attestation  │     │  - TDX Proxy    │
                 │  3. Forward if valid    │     │    on :8081     │
                 └─────────────────────────┘     └─────────────────┘
```

## Quick Start

### Using Docker Compose

```bash
# Start dashboard with PostgreSQL
docker-compose up -d

# Dashboard available at http://localhost:8080
```

### Using Docker

```bash
# Build
docker build -t attestation-dashboard .

# Run with SQLite
docker run -p 8080:8080 attestation-dashboard

# Run with PostgreSQL
docker run -p 8080:8080 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  attestation-dashboard
```

### Development

```bash
# Backend
cd app
pip install -r requirements.txt
python -m uvicorn main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

## API Endpoints

### Registration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/registrations | List all registered apps |
| POST | /api/v1/registrations | Register new app |
| GET | /api/v1/registrations/{id} | Get app details |
| PUT | /api/v1/registrations/{id} | Update app |
| DELETE | /api/v1/registrations/{id} | Delete app |

### Verification

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/verify | Full chain verification |
| POST | /api/v1/verify/baseline | Capture baseline measurements |
| GET | /api/v1/verify/history | Verification history |

### Proxy

| Method | Endpoint | Description |
|--------|----------|-------------|
| ANY | /proxy/{app_id}/{path} | Attestation-verified proxy |
| GET | /proxy/{app_id}/_status | Proxy status for app |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./attestation.db` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8080` |
| `DEBUG` | Debug mode | `false` |
| `GITHUB_TOKEN` | GitHub token for private repos | (empty) |
| `DCAP_LIBRARY_PATH` | Path to DCAP QVL library | `/usr/lib/x86_64-linux-gnu/libsgx_dcap_quoteverify.so` |
| `ATTESTATION_CACHE_TTL_SECONDS` | Cache TTL for attestations | `300` |

## Using the Proxy

Once an application is registered and has baseline measurements:

```bash
# Get the proxy URL from the registration response
PROXY_URL="http://dashboard:8080/proxy/<registration-id>"

# Access the application through the proxy
curl $PROXY_URL/api/endpoint

# Response headers include:
# X-TDX-Verified: true
# X-TDX-Verification-Time: <timestamp>
# X-TDX-DCAP-Status: OK
```

If attestation fails, the proxy returns 403 with details:

```json
{
  "error": "Attestation verification failed",
  "dcap_valid": false,
  "github_valid": true,
  "measurements_valid": false
}
```

## Self-Registering Applications

Applications can register themselves on startup. See [../sample-tdx-app](../sample-tdx-app) for an example.

```python
import httpx

registration_data = {
    "name": "my-app",
    "github_org": "my-org",
    "github_repo": "my-repo",
    "image_repository": "ghcr.io/my-org/my-app",
    "app_endpoint": "http://10.0.0.5:8080",
    "tdx_proxy_endpoint": "http://10.0.0.5:8081",
}

with httpx.Client() as client:
    resp = client.post(f"{DASHBOARD_URL}/api/v1/registrations", json=registration_data)
    registration = resp.json()

    # Capture baseline
    client.post(
        f"{DASHBOARD_URL}/api/v1/verify/baseline",
        json={"registration_id": registration["id"]}
    )
```

## Verification Chain

The dashboard performs three verification steps:

1. **DCAP Quote Verification**: Validates the TDX quote signature using Intel's Quote Verification Library
2. **GitHub Attestation**: Verifies the container image was built by GitHub Actions and matches the expected repository
3. **Measurement Comparison**: Compares the TDX measurements (MRTD, RTMR0-3) against stored baselines

All three must pass for the proxy to forward traffic.

## Notes

- **DCAP Library**: If the DCAP library is not available, the system falls back to mock verification (structural validation only)
- **Measurements**: Expected measurements are captured from a trusted first deployment; they cannot be computed from the Dockerfile alone
- **Cache**: Attestation results are cached (default 5 minutes) to avoid verification on every request
