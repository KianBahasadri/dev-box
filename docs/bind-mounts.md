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
| `/home/kian/Downloads/dev` | `/home/dev/Downloads/dev` | Read/write |
| `/home/kian/game` | `/home/dev/game` | Read/write |
| `/home/kian/hangout-automator` | `/home/dev/hangout-automator` | Read/write |

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

## Tools that bake absolute paths into a project

A mounted project is one directory with two identities: `/home/kian/<project>`
owned by `kian` on the host, `/home/dev/<project>` owned by `dev` in here. Any
tool that writes an absolute path *into* the project produces a file that only
works on the side that wrote it.

Python virtualenvs are the case that bites. `uv` records the interpreter path in
`.venv/pyvenv.cfg` and in every `.venv/bin/` shebang, so a venv built inside the
container leaves the host with a `.venv` pointing at `/home/dev/.local/share/uv/
python/...` — a directory the host user cannot even read, because `/home/dev` is
mode `700` and owned by someone else. The host then fails on any `uv` command
with:

```text
error: Failed to query Python interpreter
  Caused by: failed to canonicalize path `.../.venv/bin/python3`: Permission denied
```

Building on the host breaks the container the same way. Whichever side ran `uv`
last wins.

Give each side its own environment directory. `UV_PROJECT_ENVIRONMENT` accepts a
relative path, which `uv` resolves against each project root — so a single
value covers every mounted project, and none of them collide with the host.

Export it near the top of `~/.bashrc`, **above** the interactivity guard:

```bash
#
# ~/.bashrc
#

export UV_PROJECT_ENVIRONMENT=.venv-box

# If not running interactively, don't do anything
[[ $- != *i* ]] && return
```

The placement is the whole trick, because bash reads different files depending
on how the shell started, and this variable has to survive all of them:

| Shell | Reads | Example |
|-------|-------|---------|
| Interactive, non-login | `.bashrc` only | `incus exec node-dev -- bash`, a session already open |
| Login (interactive or not) | `.bash_profile`, which sources `.bashrc` | `incus exec node-dev -- su -l dev`, `su -l dev -c '...'` |

`.bash_profile` alone misses every non-login shell. `.bashrc` *below* the guard
misses every non-interactive one — including `su -l dev -c '...'`, which is how
scripts and agents run commands in here. Above the guard in `.bashrc` is the one
spot that covers both: the guard's `return` only ends the sourcing, so lines
before it have already run.

Add `.venv-box/` to each project's `.gitignore`.

An already-open shell keeps the environment it started with, so re-login before
trusting it:

```bash
incus exec node-dev -- su -l dev -c 'echo $UV_PROJECT_ENVIRONMENT'  # .venv-box
```

If a `.venv` does get built on the wrong side, no amount of environment fixing
repairs it — the absolute paths are already written. Delete that `.venv` and let
the losing side rebuild its own.

Like the `dev` user and the auth symlinks above, this is container-local state
that `terraform apply` does not create. Re-apply it after rebuilding the
instance.
