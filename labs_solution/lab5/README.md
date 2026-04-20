# Ansible Automation - Lab 05

This directory contains a professional Ansible implementation for system provisioning and application deployment.

## Quick Start

### Prerequisites

- Ansible 2.16+
- SSH access to target VM
- Docker Hub credentials (for app deployment)

### Installation

```bash
# Create vault password file (one-time setup)
echo "your-vault-password" > .vault_pass
chmod 600 .vault_pass

# Install dependencies (optional, for development)
pip install ansible-lint
```

### Running Playbooks

#### System Provisioning (Docker + essentials)

```bash
# First time (with vault password)
ansible-playbook playbooks/provision.yml --vault-password-file .vault_pass

# Or with prompt
ansible-playbook playbooks/provision.yml --ask-vault-pass

# Test connectivity first
ansible all -m ping --vault-password-file .vault_pass
```

#### Application Deployment

```bash
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass
```

#### View Vault Content

```bash
ansible-vault view group_vars/all.yml --vault-password-file .vault_pass
```

#### Edit Vault Content

```bash
ansible-vault edit group_vars/all.yml --vault-password-file .vault_pass
```

## Idempotency

All playbooks are idempotent:
- First run: Makes necessary changes
- Subsequent runs: No changes needed (all tasks ok)
- Safe to run multiple times

## Verification

After deployment, verify:

```bash
# Check container status
ansible webservers -a "docker ps" --vault-password-file .vault_pass

# Test health endpoint
curl http://<VM-IP>:5000/health

# Test main endpoint
curl http://<VM-IP>:5000/
```

## Documentation

See `docs/LAB05.md` for comprehensive documentation.

