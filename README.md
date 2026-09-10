# dev-box

Terraform configuration for a local development environment using Incus (LXC).

See `AGENTS.md` for agent/AI tooling notes (container access, prompt detection, etc.).

## Files

- `node-dev.tf` - Defines the `node-dev` Incus instance.
- `scripts/dev-box-enter` - Restricted host launcher for entering the existing container; see [container access](docs/container-access.md) for installation.

## Requirements

- Terraform >= 1.5
- Incus provider for Terraform

## Usage

```bash
terraform init
terraform apply
```

**Note:** This configuration mounts a local host directory into the container.
