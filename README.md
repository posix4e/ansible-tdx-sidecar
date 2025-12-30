# ansible-tdx-sidecar

Deploy any Docker application with Intel TDX (Trust Domain Extensions) attestation support using Ansible.

This toolkit provisions a TDX-enabled virtual machine with a native TDX Attestation Proxy sidecar that your containerized application can use to generate hardware-backed attestation quotes.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        TDX HOST                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     TDX VM                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │           Docker Compose Stack                       │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │  │
│  │  │  │ Your App │  │ Postgres │  │  MinIO   │          │  │  │
│  │  │  │  :8080   │  │  (opt)   │  │  (opt)   │          │  │  │
│  │  │  └────┬─────┘  └──────────┘  └──────────┘          │  │  │
│  │  └───────┼─────────────────────────────────────────────┘  │  │
│  │          │ TDX_ATTESTATION_PROXY_URL                      │  │
│  │          ▼                                                 │  │
│  │  ┌─────────────────┐                                      │  │
│  │  │  TDX Attestation│◄──── VMCALL via libtdx-attest        │  │
│  │  │     Proxy :8081 │                                      │  │
│  │  └─────────────────┘                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                         VSOCK:4050                               │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  QGS (Quote Generation Service) ◄──── Intel PCCS            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **TDX-enabled hardware** (Intel 4th Gen Xeon Scalable or newer with TDX support)
- **Ubuntu 24.04** host OS
- **Intel PCCS API Key** - Register at [Intel Trusted Services Portal](https://api.portal.trustedservices.intel.com/)
- **Ansible** installed on your control machine

## Quick Start

### 1. Setup TDX Host (One-time)

```bash
# Set your Intel PCCS API key
export INTEL_PCCS_API_KEY="your-api-key-here"

# Configure the TDX host (installs TDX kernel, QGS, PCCS)
ansible-playbook -i inventory/hosts.yml playbooks/setup-host.yml

# IMPORTANT: Reboot to enable TDX
sudo reboot
```

### 2. Deploy Your Application

```bash
# Deploy with your Docker image
ansible-playbook playbooks/deploy.yml \
  -e "app_image=your-registry/your-app:tag" \
  -e "app_port=8080"
```

### 3. Get TDX Measurements

```bash
# Extract TDX measurements for verification
ansible-playbook playbooks/measure.yml
```

## Configuration

Edit `group_vars/all.yml` to customize your deployment:

```yaml
# VM Configuration
vm_name: tdx-app
vm_memory_mb: 4096
vm_cpus: 2

# Your Application
app_image: "your-registry/your-app:latest"
app_port: 8080
app_health_check_path: /health

# Additional environment variables
app_environment:
  MY_API_KEY: "secret"
  DATABASE_URL: "postgres://..."

# Optional sidecars
enable_postgres: true
enable_minio: false
```

## Using TDX Attestation in Your Application

The TDX Attestation Proxy is available at `http://host.docker.internal:8081` from within your containers.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Check TDX availability |
| `/quote` | GET | Generate quote with default report data |
| `/quote` | POST | Generate quote with custom report data |
| `/logs` | GET | View proxy logs |

### Example: Python

```python
import os
import requests

TDX_PROXY = os.environ.get('TDX_ATTESTATION_PROXY_URL', 'http://host.docker.internal:8081')

def get_tdx_quote(report_data=None):
    """Get TDX attestation quote."""
    if report_data:
        response = requests.post(f'{TDX_PROXY}/quote', json={
            'reportData': base64.b64encode(report_data).decode()
        })
    else:
        response = requests.get(f'{TDX_PROXY}/quote')

    return response.json()

# Usage
quote = get_tdx_quote()
print(f"MRTD: {quote['measurements']['mrtd']}")
```

### Example: Node.js

```javascript
const TDX_PROXY = process.env.TDX_ATTESTATION_PROXY_URL || 'http://host.docker.internal:8081';

async function getTdxQuote() {
  const response = await fetch(`${TDX_PROXY}/quote`);
  return response.json();
}

// Usage
const quote = await getTdxQuote();
console.log(`MRTD: ${quote.measurements.mrtd}`);
```

## Playbooks

| Playbook | Description |
|----------|-------------|
| `setup-host.yml` | One-time TDX host configuration |
| `deploy.yml` | Deploy TDX VM with your application |
| `destroy.yml` | Tear down the VM |
| `measure.yml` | Extract TDX measurements |
| `status.yml` | Check deployment status |

## TDX Measurements

After running `measure.yml`, measurements are saved to `measurements.json`:

```json
{
  "mrtd": "48-byte-hex-measurement...",
  "rtmr0": "48-byte-hex-measurement...",
  "rtmr1": "48-byte-hex-measurement...",
  "rtmr2": "48-byte-hex-measurement...",
  "rtmr3": "48-byte-hex-measurement...",
  "quote_base64": "base64-encoded-quote...",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Measurement Meanings

- **MRTD**: Measurement of the Trust Domain (VM firmware and initial state)
- **RTMR0**: Runtime measurement register 0 (typically firmware)
- **RTMR1**: Runtime measurement register 1 (typically OS loader)
- **RTMR2**: Runtime measurement register 2 (typically OS kernel)
- **RTMR3**: Runtime measurement register 3 (application-defined)

## Directory Structure

```
ansible-tdx-sidecar/
├── ansible.cfg
├── inventory/
│   └── hosts.yml
├── group_vars/
│   └── all.yml                  # Configuration variables
├── playbooks/
│   ├── setup-host.yml           # Host setup
│   ├── deploy.yml               # Deploy VM
│   ├── destroy.yml              # Teardown
│   ├── measure.yml              # Get measurements
│   └── status.yml               # Check status
├── roles/
│   ├── qgs_host/                # TDX host setup
│   ├── tdx_vm/                  # VM provisioning
│   │   ├── files/
│   │   │   └── tdx-attestation-proxy.py
│   │   └── templates/
│   │       ├── docker-compose.yml.j2
│   │       ├── user-data.yml.j2
│   │       └── vm.xml.j2
│   └── tdx_attestation/         # Quote generation
└── examples/
    └── hello-world/             # Example application
```

## Examples

See the `examples/hello-world/` directory for a complete example application demonstrating TDX attestation integration.

## Troubleshooting

### TDX Not Available

```bash
# Check if TDX is initialized on the host
dmesg | grep -i tdx

# Check QGS status
systemctl status qgsd

# Check PCCS status
systemctl status pccs
```

### VM Won't Start

```bash
# Check libvirt logs
journalctl -u libvirtd

# Check VM serial console
cat /var/log/libvirt/qemu/tdx-app-serial.log
```

### Quote Generation Fails

```bash
# Check TDX proxy logs (from host)
curl http://127.0.0.1:8082/logs

# Check TDX status
curl http://127.0.0.1:8082/status
```

## License

MIT License - See LICENSE file for details.
