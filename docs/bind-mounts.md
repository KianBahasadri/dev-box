# Bind mounts

`node-dev.tf` declares `disk` devices that bind-mount host directories into the
container. `shift = "true"` enables Incus UID/GID shifting so the container's
`dev` user can access them. Individual mounts may be read-only.

## Current mounts

| Host path | Container path | Access |
|-----------|----------------|--------|
| `/home/kian/condition-assesment-report-generator` | `/home/dev/condition-assesment-report-generator` | Read/write |
| `/home/kian/clusterfork` | `/home/dev/clusterfork` | Read-only |

Host paths are machine-specific — edit them (and this table) to match your own
home directory. Add more `device` blocks in `node-dev.tf` to mount additional
project directories.

## The UID-1000 requirement

ID shifting maps container UIDs to the host. For writes to work, `dev` inside
the container and the host user that owns the source directory must share the
same numeric UID (**1000** in the standard setup).

If you see `EACCES` on write inside a mount, check both sides:

```bash
id -u kian                              # host
incus exec node-dev -- su -l dev -c id  # container
ls -ln /home/kian/<project>             # host ownership
```

Do not create another user at UID 1000 before `dev` — if that slot is taken,
`dev` will land on 1001 and bind-mounted host files owned by 1000 become
unwritable. See [container-access.md](container-access.md) for creating the
`dev` user.
