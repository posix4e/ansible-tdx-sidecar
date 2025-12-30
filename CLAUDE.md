# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ansible toolkit for deploying Docker applications with Intel TDX (Trust Domain Extensions) attestation support. Provisions TDX-enabled VMs with a native TDX Attestation Proxy sidecar that containerized applications use to generate hardware-backed attestation quotes.

## Common Commands

### Linting
```bash
ansible-lint playbooks/*.yml roles/
ansible-playbook --syntax-check playbooks/*.yml
```

### Deployment Workflow
```bash
# Setup TDX host (one-time, requires INTEL_PCCS_API_KEY env var)
ansible-playbook -i inventory/hosts.yml playbooks/setup-host.yml

# Deploy application
ansible-playbook playbooks/deploy.yml -e "app_image=your-app:tag" -e "app_port=8080"

# Check status
ansible-playbook playbooks/status.yml

# Get TDX measurements
ansible-playbook playbooks/measure.yml

# Destroy VM
ansible-playbook playbooks/destroy.yml
```

### Local Testing (no remote hosts)
```bash
ansible-playbook playbooks/deploy.yml -e "app_image=nginx:alpine" -e "app_port=8080" -e "ansible_connection=local"
```

## Architecture

### Three Core Roles

1. **qgs_host** - TDX host setup: installs TDX kernel, QGS (Quote Generation Service), PCCS, Docker, and libvirt
2. **tdx_vm** - VM provisioning: creates KVM/libvirt VMs with TDX support via cloud-init, deploys Docker Compose stack
3. **tdx_attestation** - Quote generation and measurement extraction

### TDX Attestation Proxy

`roles/tdx_vm/files/tdx-attestation-proxy.py` - Python HTTP service (port 8081 in VM, 8082 on host) providing:
- `GET /status` - Check TDX availability
- `GET /quote` and `POST /quote` - Generate attestation quotes
- `GET /logs` - View proxy logs

Uses two quote generation methods: primary libtdx-attest C library via ctypes FFI, fallback to TSM configfs.

### Template Files

All in `roles/tdx_vm/templates/`:
- `vm.xml.j2` - libvirt VM definition
- `docker-compose.yml.j2` - Application stack with optional PostgreSQL/MinIO
- `user-data.yml.j2` and `network-config.yml.j2` - cloud-init configuration

### Configuration

`group_vars/all.yml` contains all configurable variables: VM specs (memory, CPUs, disk), TDX policy, network settings, application configuration, and optional service credentials.

## Key Patterns

- Jinja2 templates generate all VM and container configurations
- Sidecar pattern: TDX Proxy runs alongside user application containers
- Playbooks are idempotent and can be re-run safely
