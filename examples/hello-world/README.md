# Hello World TDX Example

A minimal Flask application demonstrating TDX attestation integration.

## Building the Image

```bash
cd examples/hello-world/app
docker build -t your-registry/hello-world-tdx:latest .
docker push your-registry/hello-world-tdx:latest
```

## Deploying

```bash
# Copy the example configuration
cp examples/hello-world/group_vars/all.yml group_vars/all.yml

# Edit to set your image
vim group_vars/all.yml

# Deploy
ansible-playbook playbooks/deploy.yml
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Application info |
| `/health` | GET | Health check |
| `/status` | GET | TDX availability status |
| `/attest` | GET | Get TDX attestation quote |
| `/attest/custom` | POST | Get quote with custom report data |

## Testing Locally (without TDX)

You can test the application locally without TDX hardware:

```bash
cd examples/hello-world/app
pip install -r requirements.txt
python main.py
```

The `/attest` endpoint will return an error (no TDX proxy available), but all other endpoints will work.

## Example Usage

```bash
# Check health
curl http://localhost:8080/health

# Get TDX status
curl http://localhost:8080/status

# Get attestation quote
curl http://localhost:8080/attest

# Get quote with custom data
curl -X POST http://localhost:8080/attest/custom \
  -H "Content-Type: application/json" \
  -d '{"data": "my-custom-attestation-data"}'
```
