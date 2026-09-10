# Guest network isolation

On this laptop, `laptop-guard.service` loads the root-managed
`/etc/nftables/laptop-guard.nft`. This is host configuration installed separately
from Terraform. It owns only the `inet laptop_guard` table and does not replace
the firewall rules owned by UFW, Docker, Incus, LXD, or Tailscale.

The policy restricts guests on `incusbr0` and `lxdbr1` before the other firewall
managers' broad accepts. New guest connections to general host services,
private IPv4 networks, local IPv6 networks, and the Tailscale interface are
blocked. Unsolicited routed connections into those guests are also blocked.

Preserved connections include gateway DNS, DHCP, IPv6 discovery, public Internet
access and return traffic, host-initiated guest connections, and guest loopback.
Existing established connections are retained when the policy is loaded. The
host-local 8000/8001 Incus proxies and Unix Wayland proxy continue to work; they
do not need a general guest-to-host IP exception.

Live validation on September 10 checked DNS and npm HTTPS as UID1000,
PostgreSQL loopback, both development-port proxies with temporary guest
listeners, and Wayland socket availability. Temporary owned network endpoints
confirmed blocked guest-to-host/private-network connections and blocked routed
ingress, with the corresponding drop counters advancing. Temporary endpoints
were removed. Stopped LXD workloads were not started to test their future needs.

For diagnosis:

```bash
systemctl status laptop-guard.service
sudo nft list table inet laptop_guard
sudo /usr/local/sbin/laptop-guard-load check
```

If a project needs a LAN service, review and add a narrow destination/port
exception in the host policy, then reload `laptop-guard.service`. Do not restore
blanket host or LAN access merely to make one connection work. Gateway addresses
and bridge names are explicit and need updating if the networks are recreated.
The separate `lsspcnet` network retains its existing, stricter networkless ACL.

This policy limits direct network access; a guest can still contact public
Internet services. Host addresses on public LAN prefixes and guest-created
Internet tunnels require separate consideration. File shares and the display
proxy retain the boundaries documented in their own topics.
