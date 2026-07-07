# dev-box docs

- [instance.md](instance.md) — The `node-dev` Incus container resource: name, image, profile, running state.
- [bind-mounts.md](bind-mounts.md) — Host-to-container disk mounts with UID/GID shifting, and the UID-1000 requirement.
- [wayland-proxy.md](wayland-proxy.md) — The proxy device forwarding the host Wayland socket, and why it isn't a runtime-dir mount.
- [container-access.md](container-access.md) — Entering the container, the `dev` user, and recognizing pasted terminal output from host vs. dev box.
- [terraform-config.md](terraform-config.md) — Terraform version/provider constraints, lock file, and provisioning commands.

## Notes

- These docs are AI-generated, after-the-fact, and implementation-accurate
  (describing what the code does), not design-accurate (what it was meant to
  do). They may drift from intent over time.
- Information should not be repeated across files. Each topic lives in exactly
  one doc; cross-reference instead of duplicating.
- Experiments and dead-ends should get their own doc files.
