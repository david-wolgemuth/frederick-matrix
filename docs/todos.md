# frederick-matrix — TODOs

*Last updated: 2026-02-15*

### 🏷️ Status Legend
- 🔥 **HIGH PRIORITY** — Critical for user experience or stability
- ⚡ **MEDIUM PRIORITY** — Important but not blocking
- 🚫 **BLOCKED** — Cannot proceed until dependency resolved
- ⚠️ **BREAKING CHANGE** — Requires migration or will disrupt existing users
- ✅ **FIXED** — Completed and deployed
- 📋 **PENDING** — Not yet started
- 🎯 **RECOMMENDED** — Best approach among alternatives

## 📊 Summary

**Total Items:** 101 tasks (25 main tasks + 76 sub-tasks) across 7 categories
**Completed:** 3 ✅ | **In Progress:** 0 ⏳ | **Pending:** 98 📋
**High Priority:** 7 items 🔥 (stable DNS, tunnel reliability, onboarding docs, backups, tests, server_name fix)
**Blockers:** 1 🚫 (federation blocked by server_name issue)

### 📈 Progress by Category
- 🚨 **Critical/Blocking:** 0/2 complete (0%)
- 🐛 **Bugs:** 2/3 complete (67%) ████████░░
- 🏗️ **Infrastructure:** 0/6 complete (0%)
- 🌐 **GitHub Pages:** 0/4 complete (0%)
- 🌐 **Mesh/Federation:** 0/3 complete (0%)
- 🛠️ **Developer Experience:** 0/3 complete (0%)
- 📚 **Documentation:** 1/2 complete (50%) █████░░░░░
- ✨ **Nice to Have:** 0/5 complete (0%)

### 🎯 Next Actions (Recommended Order)
1. 🦆 **Set up DuckDNS + Named Tunnel** — solves both stability and network compatibility issues
2. 👥 **Create onboarding guide** — improve friend experience
3. 💾 **Implement backup script** — protect against data loss
4. 🧪 **Add tests** — prevent regressions as project grows
5. 🔗 **Fix server_name** — enable true federation

---

## 🚨 Critical / Blocking

- [ ] 🔥 **HIGH PRIORITY** | 🔍 **Tunnel is unreliable on restrictive networks** — Cloudflare quick tunnels use QUIC which is blocked on many WiFi networks (coffee shops, etc). Investigate alternatives:
  - [ ] 📋 🦆 DuckDNS + port forwarding (stable hostname, no tunnel needed if port 443/8448 open)
  - [ ] 📋 🎯 **DuckDNS + Cloudflare named tunnel** (free tier, stable URL, falls back to HTTP/2) — *Recommended path, see docs/named-tunnel.md* **[RECOMMENDED]**
  - [ ] 📋 🔐 Tailscale / Wireguard as alternative for peer-to-peer connectivity
  - [ ] 📋 🌐 ngrok (supports TCP, less QUIC-dependent)
- [ ] 🔥 **HIGH PRIORITY** | ⏰ **Tunnel URLs are ephemeral** — every restart gets a new random `trycloudflare.com` domain. Friends' Element clients break until they update homeserver URL. A stable DNS name (DuckDNS, own domain, etc.) would fix this permanently. *Note: Addressed by switching to named tunnel with stable domain.*

## 🐛 Bugs

- [x] ✅ **FIXED (2026-02-14)** | **`make publish` SHA detection bug** — `gh api` returns 404 JSON but exits 0 when using `--jq`, so the `|| echo ""` fallback never triggers. The SHA variable gets the error JSON string (non-empty), which accidentally still works but for the wrong reason. **SOLUTION:** Now properly handles 404 by piping full response through jq with `// ""` fallback.
- [x] ✅ **FIXED (2026-02-14)** | **`make tunnel-url` reports stale URLs** — greps historical docker logs, so it returns the last URL even if the tunnel died hours ago and DNS no longer resolves. **SOLUTION:** Now shows timestamp of when URL was last seen in logs, checks reachability with curl, and displays clear LIVE/UNREACHABLE status.
- [ ] 📋 **`docker compose logs` accumulates across restarts** — `tunnel-url` and `publish` both grep full log history. If container is recreated vs restarted, log behavior differs. Consider writing current URL to a file (`/tmp/tunnel-url`) on successful registration instead of log-grepping. *Note: Partially mitigated by timestamp check in `make tunnel-url`, but persisting to file would be more reliable.*
  - [ ] 📋 Create helper script to persist tunnel URL to `data/tunnel-url`
  - [ ] 📋 Update `make tunnel-url` to read from file first, fall back to logs
  - [ ] 📋 Update tunnel startup to call the helper script

## 🏗️ Infrastructure

- [ ] 🔥 **HIGH PRIORITY** | 🚀 **Stable DNS** — Replace ephemeral trycloudflare URLs with a stable hostname
  - [ ] 📋 🦆 Evaluate DuckDNS (free dynamic DNS, supports subdomains)
  - [ ] 📋 ⏰ Auto-update DNS on tunnel/IP change (cron or systemd timer)
  - [ ] 📋 📤 Update `make publish` to push stable URL (won't need to republish on every restart)
- [ ] 📋 🔒 **SSL/TLS for federation** — Matrix federation requires valid TLS on port 8448. Currently the Cloudflare tunnel handles this. Without a tunnel, need:
  - [ ] 📋 🔐 Let's Encrypt / certbot for the DuckDNS domain
  - [ ] 📋 🔄 Reverse proxy (nginx/caddy) in front of Synapse
- [ ] ⚡ **MEDIUM PRIORITY** | 💾 **Persist tunnel URL to file** — On successful tunnel creation, write URL to `data/tunnel-url` so Makefile targets don't depend on log-grepping
- [ ] 📋 🔄 **Auto-reconnect / health check** — Script or systemd unit that monitors tunnel health and restarts cloudflared (or switches to backup) when it dies
  - [ ] 📋 Create health check script that curls tunnel URL
  - [ ] 📋 Add systemd timer or cron job to run every 5 minutes
  - [ ] 📋 Auto-restart docker compose on failure
- [ ] 📋 🤔 **`make start` vs `make up` overlap** — `start.sh` runs a foreground watcher loop; `make up` now also publishes. Clarify which is canonical or merge them.
  - [ ] 📋 Document intended use case for each command
  - [ ] 📋 Consider deprecating one or merging functionality

## 🌐 GitHub Pages / Hosted Element

- [ ] 📋 🗂️ **Config caching** — After workflow deploys, browsers may cache old `config.json` with stale homeserver URL. Add cache-control headers or version-bust the config fetch in Element.
  - [ ] 📋 Add cache-busting query param (e.g., `?v=timestamp`) to config.json fetch
  - [ ] 📋 Set appropriate Cache-Control headers in GitHub Pages config
- [ ] 📋 ⏱️ **`home.html` peer loading** — Peers section fetches each peer's `server.json` but doesn't handle slow/dead peers gracefully (no timeout indicator per peer, just silent failure).
  - [ ] 📋 Add loading spinner per peer
  - [ ] 📋 Add timeout (5s?) with error indicator
  - [ ] 📋 Show last successful fetch timestamp
- [ ] 📋 🎨 **Registration flow UX** — New users need to: open Pages link → register with token. Could improve with:
  - [ ] 📋 📄 Landing page that explains what this is before dumping into Element
  - [ ] 📋 🔑 Token entry integrated into the status page
  - [ ] 📋 📱 Better mobile experience for onboarding
- [ ] 📋 📦 **Element version pinned to v1.12.10** — Should periodically update. Add a `make element-update` or note the manual process.
  - [ ] 📋 Create `make element-update` target
  - [ ] 📋 Document manual update steps in docs/operations.md

## 🌐 Mesh / Federation

- [ ] 🚫 **BLOCKED** | 🔗 **Federation not tested** — Multiple nodes discovering each other via `peers.json` is set up, but actual Matrix federation between Synapse instances hasn't been verified. **(BLOCKED by server_name issue)** Requires:
  - [ ] 📋 🏃 Two running nodes with stable URLs
  - [ ] 🚫 ⚙️ Proper `server_name` config (currently `localhost`, which won't federate)
  - [ ] 📋 🔍 `.well-known` delegation or SRV records
  - [ ] 📋 🧪 Test message sent between federated nodes
- [ ] 🔥 **HIGH PRIORITY** | ⚠️ **BREAKING CHANGE** | **`server_name: localhost` problem** — Synapse is configured with `server_name: localhost`. User IDs are `@user:localhost`. This works for single-node but blocks federation. Changing server_name later requires a fresh database. Plan migration path.
  - [ ] 📋 📝 Document migration process
  - [ ] 📋 Create migration script to backup data
  - [ ] 📋 Test server_name change in dev environment
  - [ ] 📋 Communicate breaking change to users
- [ ] 📋 🤖 **Peer discovery is manual** — `peers.json` is hand-edited. Could automate: each node publishes to a shared registry (GitHub repo, or a known "seed" node's API).
  - [ ] 📋 Design peer registry format (GitHub repo with JSON files?)
  - [ ] 📋 Create `make register-peer` to publish to registry
  - [ ] 📋 Create `make discover-peers` to pull from registry
  - [ ] 📋 Add automatic peer discovery on startup (optional)

## 🛠️ Developer Experience

- [ ] 🔥 **HIGH PRIORITY** | 🧪 **No tests** — No automated verification that the stack works after changes
  - [ ] 📋 🎭 Playwright smoke test: `make up` → register → send message → verify
  - [ ] 📋 🔄 CI: workflow that spins up Synapse, runs health check
  - [ ] 📋 📊 Test coverage reporting
  - [ ] 📋 🏷️ Version tagging and release process
- [ ] 📋 🌍 **`workshed playwright` needs Chrome** — WSL environment doesn't have Chrome installed. Either:
  - [ ] 📋 📦 Add Chrome install to setup docs
  - [ ] 📋 🎭 Use `playwright install chromium` (Playwright's bundled browser) — *Recommended* **[RECOMMENDED]**
- [ ] 📋 📝 **Makefile getting large** — Consider splitting into `scripts/` for complex targets (publish, tunnel-url) and keeping Makefile as thin wrappers.
  - [ ] 📋 Move complex bash logic to `scripts/publish.sh`
  - [ ] 📋 Move tunnel-url logic to `scripts/check-tunnel.sh`
  - [ ] 📋 Keep Makefile as simple interface layer

## 📚 Documentation

- [x] ✅ **FIXED (2026-02-14)** | **docs/ committed but not linked from README** — **SOLUTION:** Added a new "Documentation" section to README.md with direct links to all docs: quickstart, architecture, setup, operations, named-tunnel, and networking guides.
- [ ] 🔥 **HIGH PRIORITY** | 👥 **Onboarding guide for friends** — Non-technical guide: "Here's a link, here's your token, click register." Currently docs are operator-focused. **(Critical for user growth)**
  - [ ] 📋 Create `docs/onboarding.md` for end users
  - [ ] 📋 Add visual screenshots of registration flow
  - [ ] 📋 Create troubleshooting FAQ for common user issues
  - [ ] 📋 Add "getting started" video or GIF walkthrough
- [ ] ⚡ **MEDIUM PRIORITY** | 🔧 **Troubleshooting: network requirements** — Document that QUIC (UDP 7844) must be open for Cloudflare quick tunnels. List known-broken networks.
  - [ ] 📋 Create `docs/troubleshooting.md`
  - [ ] 📋 List network requirements (QUIC/UDP, firewall rules)
  - [ ] 📋 Document known incompatible networks (coffee shops, corporate WiFi)
  - [ ] 📋 Add fallback options (named tunnel, Tailscale)

## ✨ Nice to Have

- [ ] 📋 🤖 **Matrix bot** — Auto-welcome bot in `#general`, bridge to other services
  - [ ] 📋 Research Matrix bot frameworks (matrix-nio, mautrix)
  - [ ] 📋 Create welcome bot that greets new users
  - [ ] 📋 Add bridge to Discord/Slack (optional)
  - [ ] 📋 Add admin commands for room management
- [ ] 🔥 **HIGH PRIORITY** | 💾 **Backup/restore** — Script to backup Synapse SQLite DB + signing keys **(IMPORTANT for data safety)**
  - [ ] 📋 Create `scripts/backup.sh`
  - [ ] 📋 Backup SQLite database
  - [ ] 📋 Backup signing keys from `data/`
  - [ ] 📋 Upload to remote storage (rsync, rclone, etc.)
  - [ ] 📋 Create `scripts/restore.sh` for disaster recovery
  - [ ] 📋 Add cron job for automated daily backups
- [ ] 📋 🏠 **Multiple rooms auto-creation** — Currently relies on `auto_join_rooms` config. Add a `make rooms` target to create and configure rooms programmatically.
  - [ ] 📋 Create room creation script using Matrix API
  - [ ] 📋 Define default room set (general, announcements, support, etc.)
  - [ ] 📋 Set room permissions and topics
- [ ] 📋 📊 **Monitoring dashboard** — Expose Synapse metrics (Prometheus endpoint) + simple uptime tracking
  - [ ] 📋 Enable Synapse Prometheus metrics
  - [ ] 📋 Set up Grafana dashboard
  - [ ] 📋 Add uptime monitoring (UptimeRobot, custom script)
  - [ ] 📋 Email/Slack alerts on downtime
- [ ] 📋 📱 **Mobile-friendly status page** — `home.html` works but could be more polished on mobile
  - [ ] 📋 Responsive CSS improvements
  - [ ] 📋 Touch-friendly buttons
  - [ ] 📋 Progressive Web App (PWA) manifest
