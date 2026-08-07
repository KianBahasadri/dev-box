# The `node-dev` instance

Defined in `node-dev.tf` as an `incus_instance` resource.

| Attribute | Value |
|-----------|-------|
| Name      | `node-dev` |
| Image     | `images:archlinux/current/amd64` |
| Profile   | `default` |
| State     | Kept running (`running = true`) |

The resource declares two devices — a disk mount for project directories and a
Wayland socket proxy. Those are documented separately in
[bind-mounts.md](bind-mounts.md) and [wayland-proxy.md](wayland-proxy.md).

## The image ships without a timezone

The Arch image has no `/etc/localtime` and no `/etc/timezone`. Anything that
resolves the local zone — `tzlocal`, and so APScheduler and much of the Python
scheduling ecosystem — falls back to UTC and warns:

```text
UserWarning: Can not find any timezone configuration, defaulting to UTC.
```

A project that promotes warnings to errors (pytest's `filterwarnings = ["error"]`
does) then cannot even import its app in here, while passing on the host. Point
`/etc/localtime` at the host's zone once:

```bash
incus exec node-dev -- ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime
```

Like the `dev` user in [container-access.md](container-access.md), this is
container-local state that `terraform apply` does not create.
