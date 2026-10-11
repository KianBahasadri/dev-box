# Warframe Toolkit

The project uses the read/write mount listed in [bind-mounts.md](bind-mounts.md).
It is the existing host checkout, including its Git repository and uncommitted
edits. Changes made on either side are visible on the other.

## Local server ports

`node-dev.tf` declares two localhost-only Incus proxy devices:

| Device | Host listener | Container destination | Use |
|--------|---------------|-----------------------|-----|
| `port-5173` | `127.0.0.1:5173` | `127.0.0.1:5173` | Vite development and browser tests |
| `port-4173` | `127.0.0.1:4173` | `127.0.0.1:4173` | Production preview |

The project's existing commands bind to loopback and work with these proxies;
no `--host 0.0.0.0` flag or firewall exception is needed. Use
**http://127.0.0.1:5173/** in the host browser to retain the inventory already
saved at that origin. Both Vite modes also serve the live drop-table endpoint.

## Activate on an existing container

Changing Incus devices requires host administrator access; the restricted
`dev` launcher only enters an existing container. See
[container-access.md](container-access.md).

Stop any host Vite server listening on 5173 or 4173 before adding the matching
proxy. For the running container, an administrator can apply just these new
devices without restarting it or applying unrelated Terraform changes:

```bash
sudo incus --force-local --project default config device add node-dev warframe-toolkit disk \
  source=/home/kian/warframe-toolkit path=/home/dev/warframe-toolkit shift=true
sudo incus --force-local --project default config device add node-dev port-5173 proxy \
  listen=tcp:127.0.0.1:5173 connect=tcp:127.0.0.1:5173
sudo incus --force-local --project default config device add node-dev port-4173 proxy \
  listen=tcp:127.0.0.1:4173 connect=tcp:127.0.0.1:4173
```

Run these once. If a named device already exists, inspect it rather than remove
or replace it. The declarations in `node-dev.tf` match these devices, so the
next normal Terraform refresh picks them up. Terraform on a fresh setup also
creates them through the repository's usual provisioning workflow.

## Develop

From a host terminal:

```bash
cd ~/warframe-toolkit
dev
```

The launcher lands in `/home/dev/warframe-toolkit` after the mount is active.
Inside the container:

```bash
pwd                       # /home/dev/warframe-toolkit
node --version            # Requires Node 22.18+; npm must also be installed
npm ci                    # First setup or after dependency changes
npm run dev
```

Use the container for dependency installation and build commands from now on.
`node_modules` and generated files live in the shared checkout. Run one server
per port; the host proxy owns the host port while Vite listens inside the box.

For a production preview, run `npm run build` followed by `npm run preview`
inside the container, then open **http://127.0.0.1:4173/** on the host.

## Verification and browser tests

Inside the mounted checkout:

```bash
npm test
npm run build
```

Browser tests use `/usr/bin/chromium` by default. If Chromium is not installed
in the container, install the browser matching the project's Playwright version
into the container user's cache and pass its path explicitly:

```bash
npx playwright install chromium
CHROMIUM_PATH="$(node --input-type=module -e 'import { chromium } from "@playwright/test"; console.log(chromium.executablePath())')" npm run test:browser
```

Playwright may report missing system libraries; an administrator must install
those inside the container using its distribution's package manager. The browser
cache is container-local and does not need another host mount. Browser tests can
reuse a Vite server already running in the container or start one automatically.
