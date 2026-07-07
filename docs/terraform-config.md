# Terraform configuration

## Version & provider constraints

From `node-dev.tf`:

- `required_version = ">= 1.5.0"`
- Provider `lxc/incus`, version `~> 1.1`.

`.terraform.lock.hcl` pins the Incus provider to `1.1.1` with its full hash
set. This file is maintained automatically by `terraform init` — manual edits
may be lost on future runs.

## Requirements

- Terraform >= 1.5
- Incus installed and configured on the host
- Terraform Incus provider (`lxc/incus` ~> 1.1)

## Provisioning

```bash
terraform init
terraform apply
```

`terraform apply` creates the container and bind mounts only. It does **not**
create the `dev` user or configure shell prompts — those are set up separately
after provisioning (see [container-access.md](container-access.md)).

## Ignored files

`.gitignore` excludes Terraform state and provider directories:

- `.terraform/`
- `*.tfstate`, `*.tfstate.*`
- `crash.log`, `crash.*.log`
- Override files (`override.tf`, `*_override.tf`, etc.)
- Editor/OS files (`.DS_Store`, `*.swp`, `.idea/`, `.vscode/`)
