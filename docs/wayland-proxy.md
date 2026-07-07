# Wayland socket proxy

`node-dev.tf` defines a `proxy` device (`wayland-proxy`) that forwards only the
host's Wayland socket (`/run/user/1000/wayland-0`) to `/mnt/wayland-0` inside
the container, so GUI apps run against the host compositor.

## Why a proxy, not a mount

This is deliberately **not** a disk mount of `/run/user/1000`. The full runtime
dir would also expose the host session's D-Bus, ssh-agent, gpg-agent, and
PipeWire sockets to the container. The proxy device additionally:

- survives compositor restarts, and
- does not block container startup when no host session exists yet (e.g.
  autostart after reboot, before login).

## Device properties

```hcl
bind    = "instance"
connect = "unix:/run/user/1000/wayland-0"
listen  = "unix:/mnt/wayland-0"
uid  = "1000"   # listening socket ownership inside the container
gid  = "1000"
mode = "0600"
"security.uid" = "1000"   # host-side connections run as the session owner
"security.gid" = "1000"
```

`security.uid`/`security.gid` run host-side connections as the session owner
(1000) so the proxy can traverse `/run/user/1000` (mode 0700) after dropping
privileges.

## Container-side environment

`dev`'s `~/.bashrc` (not versioned in this repo) sets:

- `WAYLAND_DISPLAY=/mnt/wayland-0` — an absolute path, so clients don't need a
  shared `XDG_RUNTIME_DIR`.
- `XDG_SESSION_TYPE=wayland`.
- Fallback `XDG_RUNTIME_DIR=/tmp/runtime-dev` when logind hasn't provided one.

No `gpu` device is passed through, so apps use software rendering (`wl_shm`).

## Why `XDG_SESSION_TYPE=wayland` matters for Electron

Recent Electron (v43+) ignores `ELECTRON_OZONE_PLATFORM_HINT` and
`app.commandLine.appendSwitch("ozone-platform-hint", ...)`. The ozone platform
is chosen from the session type (or an explicit `--ozone-platform=wayland` CLI
flag) before the app's main script runs. Without `XDG_SESSION_TYPE=wayland`,
Electron tries X11 and dies with `Missing X server or $DISPLAY`.

## Quick test

From inside the container:

```bash
incus exec node-dev -- su -l dev -c 'WAYLAND_DISPLAY=/mnt/wayland-0 wayland-info'
```
