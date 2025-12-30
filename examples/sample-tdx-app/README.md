# Sample TDX Application

A demonstration application showing how to build TDX-aware applications that self-register with the attestation dashboard.

## Features

- Self-registers with the attestation dashboard on startup
- Captures baseline TDX measurements automatically
- Provides sample API endpoints accessible via the attestation proxy
- Integrates with the TDX attestation proxy for quote generation

## Quick Start

### 1. Build and Push the Image

```bash
# From the repository root
docker build -t your-registry/sample-tdx-app:latest examples/sample-tdx-app
docker push your-registry/sample-tdx-app:latest
```

### 2. Configure Deployment

Edit `group_vars/all.yml` with your settings:

```yaml
app_image: "your-registry/sample-tdx-app:latest"
app_environment:
  DASHBOARD_URL: "http://your-dashboard:8080"
  GITHUB_ORG: "your-org"
  GITHUB_REPO: "your-repo"
  IMAGE_REPO: "your-registry/sample-tdx-app"
```

### 3. Deploy to TDX VM

```bash
# From the repository root
ansible-playbook playbooks/deploy.yml \
  -e "@examples/sample-tdx-app/group_vars/all.yml"
```

### 4. Verify Registration

The application will automatically:
1. Start in the TDX VM
2. Contact the dashboard to register itself
3. Capture baseline measurements
4. Be accessible via the attestation proxy

Check the dashboard UI or API to see the registered application.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DASHBOARD_URL` | URL of the attestation dashboard | `http://dashboard:8080` |
| `APP_NAME` | Application name for registration | `sample-tdx-app` |
| `APP_PORT` | Port the application listens on | `8080` |
| `APP_HOST` | Override host IP for registration | (auto-detect) |
| `GITHUB_ORG` | GitHub organization for attestation | (empty) |
| `GITHUB_REPO` | GitHub repository name | (empty) |
| `IMAGE_REPO` | Container image repository | (empty) |
| `IMAGE_TAG` | Container image tag | `latest` |
| `IMAGE_DIGEST` | Image digest for GitHub attestation | (empty) |
| `CAPTURE_BASELINE` | Capture measurements on registration | `true` |
| `REGISTRATION_RETRIES` | Number of registration attempts | `5` |
| `REGISTRATION_RETRY_DELAY` | Seconds between retries | `5` |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Application info and endpoints |
| `GET /health` | Health check |
| `GET /api/data` | Sample protected data |
| `GET /api/whoami` | Application identity info |
| `GET /attest` | Get TDX attestation quote |

## Accessing via Proxy

Once registered, access the application through the attestation proxy:

```bash
# Get the proxy URL from the dashboard
PROXY_URL="http://dashboard:8080/proxy/<registration-id>"

# Access the application (attestation verified automatically)
curl $PROXY_URL/api/data

# Response includes verification headers:
# X-TDX-Verified: true
# X-TDX-Verification-Time: 2024-01-15T10:30:00Z
```

## Building Your Own TDX Application

To add self-registration to your own application:

1. Copy `app/register.py` to your application
2. Add `httpx` to your dependencies
3. Call `self_register()` on application startup
4. Set the required environment variables in your deployment

```python
from register import self_register

# In your application startup
registration = self_register()
if registration:
    print(f"Registered with ID: {registration['id']}")
```
