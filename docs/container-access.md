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

Use `dev` from a host Bash terminal. The host launcher preserves a directory
under `/home/kian` when its corresponding `/home/dev` directory exists inside
the container; otherwise it starts in `/home/dev`. It opens the same interactive,
non-login Bash environment as the original shortcut, including the container's
`.bashrc`, project environment, and Wayland setup. Paths outside `/home/kian`
also start in `/home/dev`.

`dev` uses passwordless sudo for **one fixed launcher**, not for Incus itself:

```bash
dev() {
  if (( $# != 0 )); then
    printf 'Usage: dev\n' >&2
    return 2
  fi
  local dev_status
  /usr/bin/sudo -- /usr/local/sbin/dev-box-enter
  dev_status=$?
  printf '\n'
  return "$dev_status"
}
```

The launcher is maintained in `scripts/dev-box-enter` and installed on the
**host** at `/usr/local/sbin/dev-box-enter`, owned by root and not writable by
ordinary users. Its no-argument sudo rule lives at
`/etc/sudoers.d/dev-box-enter`. Install or update both with the reviewed installer:

```bash
sudo /usr/bin/python3 -I /home/kian/dev-box/scripts/install-dev-launcher.py
```

The installer validates sudoers before and after installation and restores the
previous files if installation fails. It does not change group memberships,
container configuration, or services. After installing, replace the host's
`dev()` function with the definition above and open a new terminal.

The privileged launcher fixes the local Incus daemon, `default` project,
`node-dev` instance, container UID/GID 1000, and shell. It replaces the host
environment and uses an isolated root-owned configuration directory at
`/etc/dev-box-launcher`. Only a validated terminal type and the actual current
directory can vary; the directory is passed as data to a shell running inside
the container as `dev`. Host shell initialization and user Incus aliases are
never used by the privileged launcher.

The existing instance must already be running. An administrator handles its
configuration and start/stop operations separately. Do not grant passwordless
access to arbitrary `incus` commands or make the installed launcher writable by
the desktop user. This entry mechanism does not require `incus-admin` membership.
It retains the existing container mounts and their access permissions.

To check the installation after a new login:

```bash
sudo -n -l /usr/local/sbin/dev-box-enter
dev
# Inside the dev box:
id       # uid=1000(dev), gid=1000(dev)
pwd      # mapped project directory or /home/dev
```

The launcher rejects arguments; `sudo -n /usr/local/sbin/dev-box-enter anything`
must fail. Security tests run without root or an Incus daemon:

```bash
python3 -I -m unittest discover -s tests -p test_dev_launcher.py -v
```

For deliberate administration before the launcher is installed, an
administrator can enter using:

```bash
sudo incus --force-local --project default exec node-dev -- su -l dev
```

That command opens a login shell and requires ordinary administrative authority.
Running the repository's Terraform providers/provisioners with `sudo` is not a
substitute for designing the separate administration workflow.

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
