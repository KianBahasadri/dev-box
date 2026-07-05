# Agent guide: dev-box

This repository defines a local development environment using [Incus](https://linuxcontainers.org/incus/) (LXC) and Terraform.

See `README.md` for a brief human-oriented overview.

## Repository layout

| File | Purpose |
|------|---------|
| `node-dev.tf` | Terraform config for the `node-dev` Incus container |
| `README.md` | Human-oriented setup and usage notes |
| `AGENTS.md` | Agent/AI tooling guide (this file) |
| `CLAUDE.md` | Symlink to `AGENTS.md` |

## What it provisions

- **Instance name:** `node-dev`
- **Image:** `images:archlinux/current/amd64`
- **Profile:** `default`
- **State:** Kept running (`running = true`)

### Mounted directories

Host paths are bind-mounted into the container with UID/GID shifting (`shift = "true"`) so the `dev` user can read and write them.

ID shifting maps container UIDs to the host. For this to work, `dev` inside the container and the host user that owns the source directory must share the same numeric UID (**1000** in the standard setup). If you see `EACCES` on write inside a mount, check both sides:

```bash
id -u kian                              # host
incus exec node-dev -- su -l dev -c id  # container
ls -ln /home/kian/<project>             # host ownership
```

Host paths in `node-dev.tf` are machine-specific — edit them (and the table below) to match your own home directory.

| Host path | Container path |
|-----------|----------------|
| `/home/kian/condition-assesment-report-generator` | `/home/dev/condition-assesment-report-generator` |

Add more `device` blocks in `node-dev.tf` to mount additional project directories.

## Requirements

- Terraform >= 1.5
- Incus installed and configured on the host
- Terraform Incus provider (`lxc/incus` ~> 1.1)

## Provisioning

```bash
terraform init
terraform apply
```

`terraform apply` creates the container and bind mounts only. It does **not** create the `dev` user or configure shell prompts — those are set up separately after provisioning.

## The dev box container

### Default user

The working user inside the container is **`dev`** with UID/GID **1000**. This must match the numeric UID of the host user that owns bind-mounted project directories (e.g. `kian` at 1000 on the host), or shifted mounts will be read-only for `dev`.

`terraform apply` does not create this user. After provisioning, create `dev` at UID 1000 before adding bind mounts you intend to write to:

```bash
incus exec node-dev -- useradd -m -u 1000 -g 1000 dev
```

Do not create another user at UID 1000 first — if that slot is taken, `dev` will land on 1001 and bind-mounted host files owned by 1000 become unwritable (`EACCES`).

Verify:

```bash
incus exec node-dev -- su -l dev -c id
# uid=1000(dev) gid=1000(dev)
```

### Entering the dev box

Agents can enter the container to inspect the environment, run commands, or debug issues:

```bash
incus exec node-dev -- su -l dev
```

This drops you into a login shell as `dev` with the usual environment (`~/.bashrc`, etc.).

### Recognizing pasted terminal output

When the user pastes terminal output, check the prompt to tell whether it came from **inside the dev box** or from the **host**.

Both environments share the same prompt style (time + directory depth indicator), but the **dev box prompt includes the hostname** in brackets at the start.

Prompt configuration lives in `~/.bashrc` on the host and inside the container — it is **not** versioned in this repository and may drift. The values below reflect the current setup.

**Inside the dev box** (`~/.bashrc` on `dev@node-dev`):

```bash
PS1='\[\e[34m\][\[\e[32m\]\h\[\e[34m\]]\[\e[0m\] \[\e[38;5;218m\]\A\[\e[0m\] \[\e[38;5;204m\]${PROMPT_LOC}\[\e[0m\]\[\e[38;5;250m\]\$ \[\e[0m\]'
```

Rendered example:

```text
[node-dev] 14:32:05 2/my-project$ 
```

- `[node-dev]` — blue brackets, green hostname (`\h` resolves to `node-dev`)
- `\A` — current time (24-hour)
- `${PROMPT_LOC}` — directory depth + current directory name (e.g. `~`, `/`, `2/my-project`)
- Trailing `$`

**On the host** (`~/.bashrc` on the physical machine):

```bash
PS1='\[\e[38;5;218m\]\A\[\e[0m\] \[\e[38;5;204m\]${PROMPT_LOC}\[\e[0m\]\[\e[38;5;250m\]\$ \[\e[0m\]'
```

Rendered example:

```text
14:32:05 2/my-project$ 
```

Same time and `${PROMPT_LOC}` format, but **no `[hostname]` prefix**. If pasted output starts with `[node-dev]`, it originated inside the container.

Both prompts use a `PROMPT_COMMAND` hook (`__prompt_depth`) that sets `PROMPT_LOC` based on directory nesting depth.

**Fallback cues** when the prompt prefix is missing or ambiguous (e.g. `PS1` unset, output piped through a tool, or the instance was renamed):

- Run `hostname` — `node-dev` indicates the container
- Paths under `/home/dev/` (vs `/home/kian/` on the host)
- Context from the surrounding conversation (user said they ran `incus exec`, etc.)
