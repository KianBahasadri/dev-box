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
