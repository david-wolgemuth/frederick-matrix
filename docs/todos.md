# frederick-matrix — TODOs

## Critical / Blocking

- [ ] 🔍 **Tunnel is unreliable on restrictive networks** — Cloudflare quick tunnels use QUIC which is blocked on many WiFi networks (coffee shops, etc). Investigate alternatives:
  - [ ] DuckDNS + port forwarding (stable hostname, no tunnel needed if port 443/8448 open)
  - [ ] 📋 DuckDNS + Cloudflare named tunnel (free tier, stable URL, falls back to HTTP/2) — *Recommended path, see docs/named-tunnel.md*
  - [ ] Tailscale / Wireguard as alternative for peer-to-peer connectivity
  - [ ] ngrok (supports TCP, less QUIC-dependent)
- [ ] 🔍 **Tunnel URLs are ephemeral** — every restart gets a new random `trycloudflare.com` domain. Friends' Element clients break until they update homeserver URL. A stable DNS name (DuckDNS, own domain, etc.) would fix this permanently. *Note: Addressed by switching to named tunnel with stable domain.*

## Bugs

- [x] ✅ **`make publish` SHA detection bug** — `gh api` returns 404 JSON but exits 0 when using `--jq`, so the `|| echo ""` fallback never triggers. The SHA variable gets the error JSON string (non-empty), which accidentally still works but for the wrong reason. **FIXED:** Now properly handles 404 by piping full response through jq with `// ""` fallback.
- [x] ✅ **`make tunnel-url` reports stale URLs** — greps historical docker logs, so it returns the last URL even if the tunnel died hours ago and DNS no longer resolves. **FIXED:** Now shows timestamp of when URL was last seen in logs, checks reachability with curl, and displays clear LIVE/UNREACHABLE status.
- [ ] 💡 **`docker compose logs` accumulates across restarts** — `tunnel-url` and `publish` both grep full log history. If container is recreated vs restarted, log behavior differs. Consider writing current URL to a file (`/tmp/tunnel-url`) on successful registration instead of log-grepping. *Note: Partially mitigated by timestamp check in `make tunnel-url`, but persisting to file would be more reliable.*

## Infrastructure

- [ ] 🚀 **Stable DNS** — Replace ephemeral trycloudflare URLs with a stable hostname
  - [ ] Evaluate DuckDNS (free dynamic DNS, supports subdomains)
  - [ ] Auto-update DNS on tunnel/IP change (cron or systemd timer)
  - [ ] Update `make publish` to push stable URL (won't need to republish on every restart)
- [ ] 🔒 **SSL/TLS for federation** — Matrix federation requires valid TLS on port 8448. Currently the Cloudflare tunnel handles this. Without a tunnel, need:
  - [ ] Let's Encrypt / certbot for the DuckDNS domain
  - [ ] Reverse proxy (nginx/caddy) in front of Synapse
- [ ] 💾 **Persist tunnel URL to file** — On successful tunnel creation, write URL to `data/tunnel-url` so Makefile targets don't depend on log-grepping
- [ ] 🔄 **Auto-reconnect / health check** — Script or systemd unit that monitors tunnel health and restarts cloudflared (or switches to backup) when it dies
- [ ] 🤔 **`make start` vs `make up` overlap** — `start.sh` runs a foreground watcher loop; `make up` now also publishes. Clarify which is canonical or merge them.

## GitHub Pages / Hosted Element

- [ ] 🌐 **Config caching** — After workflow deploys, browsers may cache old `config.json` with stale homeserver URL. Add cache-control headers or version-bust the config fetch in Element.
- [ ] ⏱️ **`home.html` peer loading** — Peers section fetches each peer's `server.json` but doesn't handle slow/dead peers gracefully (no timeout indicator per peer, just silent failure).
- [ ] 🎨 **Registration flow UX** — New users need to: open Pages link → register with token. Could improve with:
  - [ ] Landing page that explains what this is before dumping into Element
  - [ ] Token entry integrated into the status page
- [ ] 📦 **Element version pinned to v1.12.10** — Should periodically update. Add a `make element-update` or note the manual process.

## Mesh / Federation

- [ ] 🔗 **Federation not tested** — Multiple nodes discovering each other via `peers.json` is set up, but actual Matrix federation between Synapse instances hasn't been verified. Requires:
  - [ ] Two running nodes with stable URLs
  - [ ] Proper `server_name` config (currently `localhost`, which won't federate)
  - [ ] `.well-known` delegation or SRV records
- [ ] ⚠️ **`server_name: localhost` problem** — Synapse is configured with `server_name: localhost`. User IDs are `@user:localhost`. This works for single-node but blocks federation. Changing server_name later requires a fresh database. Plan migration path.
- [ ] 🤖 **Peer discovery is manual** — `peers.json` is hand-edited. Could automate: each node publishes to a shared registry (GitHub repo, or a known "seed" node's API).

## Developer Experience

- [ ] 🧪 **No tests** — No automated verification that the stack works after changes
  - [ ] Playwright smoke test: `make up` → register → send message → verify
  - [ ] CI: workflow that spins up Synapse, runs health check
- [ ] 🌍 **`workshed playwright` needs Chrome** — WSL environment doesn't have Chrome installed. Either:
  - [ ] Add Chrome install to setup docs
  - [ ] Use `playwright install chromium` (Playwright's bundled browser)
- [ ] 📝 **Makefile getting large** — Consider splitting into `scripts/` for complex targets (publish, tunnel-url) and keeping Makefile as thin wrappers.

## Documentation

- [x] ✅ **docs/ committed but not linked from README** — **FIXED:** Added a new "Documentation" section to README.md with direct links to all docs: quickstart, architecture, setup, operations, named-tunnel, and networking guides.
- [ ] 👥 **Onboarding guide for friends** — Non-technical guide: "Here's a link, here's your token, click register." Currently docs are operator-focused.
- [ ] 🔧 **Troubleshooting: network requirements** — Document that QUIC (UDP 7844) must be open for Cloudflare quick tunnels. List known-broken networks.

## Nice to Have

- [ ] 🤖 **Matrix bot** — Auto-welcome bot in `#general`, bridge to other services
- [ ] 💾 **Backup/restore** — Script to backup Synapse SQLite DB + signing keys
- [ ] 🏠 **Multiple rooms auto-creation** — Currently relies on `auto_join_rooms` config. Add a `make rooms` target to create and configure rooms programmatically.
- [ ] 📊 **Monitoring dashboard** — Expose Synapse metrics (Prometheus endpoint) + simple uptime tracking
- [ ] 📱 **Mobile-friendly status page** — `home.html` works but could be more polished on mobile
