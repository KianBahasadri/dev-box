# Bind mounts

`node-dev.tf` declares `disk` devices that bind-mount host directories into the
container. `shift = "true"` enables Incus UID/GID shifting so the container's
`dev` user can access them. Individual mounts may be read-only.

## Current mounts

| Host path | Container path | Access |
|-----------|----------------|--------|
| `/home/kian/condition-assesment-report-generator` | `/home/dev/condition-assesment-report-generator` | Read/write |
| `/home/kian/clusterfork` | `/home/dev/clusterfork` | Read-only |
| `/home/kian/.local/share/clusterfork-auth` | `/home/dev/.local/share/clusterfork-auth` | Read-only |
| `/home/kian/game` | `/home/dev/game` | Read/write |

Host paths are machine-specific — edit them (and this table) to match your own
home directory. Add more `device` blocks in `node-dev.tf` to mount additional
project directories.

The Clusterfork auth-store mount lets the container follow host-side Codex and
Cursor account changes without remounting individual `auth.json` files. The
container's agent auth paths are symlinks into this store. Because the mount is
read-only, rotate accounts and refresh tokens on the host.

After creating the container's `dev` user, create those links once:

```bash
incus exec node-dev -- su -l dev -c '
  mkdir -p ~/.codex ~/.config/cursor
  ln -s ../.local/share/clusterfork-auth/codex/current ~/.codex/auth.json
  ln -s ../../.local/share/clusterfork-auth/cursor/current ~/.config/cursor/auth.json
'
```

The commands intentionally stop if an auth path already exists so they cannot
overwrite container-local credentials.

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
