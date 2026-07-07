# Container access

## The `dev` user

The working user inside the container is **`dev`** with UID/GID **1000**. This
must match the numeric UID of the host user that owns bind-mounted project
directories (see [bind-mounts.md](bind-mounts.md)), or shifted mounts will be
read-only for `dev`.

`terraform apply` does **not** create this user. After provisioning, create
`dev` at UID 1000 before adding bind mounts you intend to write to:

```bash
incus exec node-dev -- useradd -m -u 1000 -g 1000 dev
```

Verify:

```bash
incus exec node-dev -- su -l dev -c id
# uid=1000(dev) gid=1000(dev)
```

## Entering the container

```bash
incus exec node-dev -- su -l dev
```

Drops into a login shell as `dev` with the usual environment (`~/.bashrc`,
etc.).

## Recognizing pasted terminal output

When the user pastes terminal output, check the prompt to tell whether it came
from **inside the dev box** or from the **host**.

Both environments share the same prompt style (time + directory depth
indicator), but the **dev box prompt includes the hostname** in brackets at the
start. Prompt config lives in `~/.bashrc` on the host and inside the container
— it is **not** versioned in this repository and may drift. The values below
reflect the current setup.

**Inside the dev box** (`~/.bashrc` on `dev@node-dev`):

```bash
PS1='\[\e[34m\][\[\e[32m\]\h\[\e[34m\]]\[\e[0m\] \[\e[38;5;218m\]\A\[\e[0m\] \[\e[38;5;204m\]${PROMPT_LOC}\[\e[0m\]\[\e[38;5;250m\]\$ \[\e[0m\]'
```

Rendered:

```text
[node-dev] 14:32:05 2/my-project$
```

- `[node-dev]` — blue brackets, green hostname (`\h` resolves to `node-dev`)
- `\A` — current time (24-hour)
- `${PROMPT_LOC}` — directory depth + current directory name (e.g. `~`, `/`,
  `2/my-project`)
- Trailing `$`

**On the host** (`~/.bashrc` on the physical machine):

```bash
PS1='\[\e[38;5;218m\]\A\[\e[0m\] \[\e[38;5;204m\]${PROMPT_LOC}\[\e[0m\]\[\e[38;5;250m\]\$ \[\e[0m\]'
```

Rendered:

```text
14:32:05 2/my-project$
```

Same time and `${PROMPT_LOC}` format, but **no `[hostname]` prefix**. If pasted
output starts with `[node-dev]`, it originated inside the container.

Both prompts use a `PROMPT_COMMAND` hook (`__prompt_depth`) that sets
`PROMPT_LOC` based on directory nesting depth.

**Fallback cues** when the prompt prefix is missing or ambiguous (e.g. `PS1`
unset, output piped through a tool, or the instance was renamed):

- Run `hostname` — `node-dev` indicates the container.
- Paths under `/home/dev/` (vs `/home/kian/` on the host).
- Context from the surrounding conversation (user said they ran `incus exec`,
  etc.).
