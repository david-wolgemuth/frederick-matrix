# Day-to-Day Operations

## Makefile Commands

```
make help               Show all commands
```

### Lifecycle

```
make up                 Start all services, wait for tunnel, publish URL to GitHub
make down               Stop everything
make start              Start + long-running tunnel URL watcher (foreground)
make tunnel             Force-recreate cloudflared for a new URL, publish to GitHub
make logs               Follow container logs
```

### Status & Diagnostics

```
make status             Full verbose status (docker, localhost, tunnel, Pages)
make status-quick       Summary status (one line per check)
make status-docker      Docker containers and images only
make status-localhost   Synapse + Element localhost checks only
make status-tunnel      Tunnel URL, DNS resolution, and liveness only
make status-pages       GitHub Pages endpoints only
```

`make status` runs `scripts/status.py` which checks:

| Section | What it tests |
|---------|--------------|
| Docker | `docker compose ps`, images, recent cloudflared logs |
| Localhost | Synapse API (`localhost:8008`), Element (`localhost:8080`), Element `config.json` |
| Tunnel | Extracts URL from logs, DNS resolution, hits `/_matrix/client/versions` via tunnel |
| Pages | Element, `config.json`, `server.json`, `peers.json`, `home.html` on `<you>.github.io` |

### Tunnel Management

```
make tunnel             Force-recreate cloudflared for a new URL, publish to GitHub
make tunnel-url         Show current tunnel URL and verify it's live (DNS + HTTP)
make publish            Push current tunnel URL to server.json on GitHub
```

`make tunnel` uses `docker compose up -d --force-recreate cloudflared` (not `restart`) to ensure a brand new container and a fresh quick tunnel URL. A simple `restart` reuses the same container and may reconnect to a dead DNS entry.

### Token Management

```
make create-token       Create a single-use token (expires 7 days)
make list-tokens        List all registration tokens
```

For more options use the CLI directly:

```bash
# Unlimited uses, never expires
python3 mesh-admin/mesh_admin.py create-token --uses 0

# 5 uses, expires in 30 days
python3 mesh-admin/mesh_admin.py create-token --uses 5 --expires 30d

# Revoke a token
python3 mesh-admin/mesh_admin.py revoke-token <token>
```

### Setup (one-time)

```
make setup              Full first-time setup
make gh-setup           Enable GitHub Pages (workflow-based deployment)
make element-download   Download Element Web
make element-configure  Copy configs into element/
make synapse-generate   Generate Synapse homeserver.yaml
make synapse-configure  Enable registration + auto-join rooms
make admin-user         Create admin user (admin/admin)
```

## Common Scenarios

### "I restarted my machine"

```bash
make up
```

This starts all services, waits for the new tunnel URL, and publishes it.

### "I want a new tunnel URL"

```bash
make tunnel
```

Force-recreates the cloudflared container to get a fresh URL, then publishes it.

### "My tunnel URL is stale on GitHub Pages"

```bash
make publish
```

Re-reads the current tunnel URL from cloudflared logs and pushes to GitHub.

### "I want to check if everything is working"

```bash
make status          # full verbose output
make status-quick    # one-line-per-check summary
make status-tunnel   # just check the tunnel
```

### "I want to invite someone"

```bash
# Create a token
make create-token

# Or for an unlimited token
python3 mesh-admin/mesh_admin.py create-token --uses 0

# Share with them:
# 1. The token
# 2. Your GitHub Pages link: https://<you>.github.io/frederick-matrix/
#    (Element is pre-configured with your homeserver — they just register)
```

### "A peer can't connect to me"

1. Check full status: `make status`
2. Check your tunnel specifically: `make status-tunnel`
3. If DNS fails, recreate the tunnel: `make tunnel`
4. Check your network — some restrictive networks (e.g., coffee shop WiFi with client isolation) block cloudflared's outbound connections. A phone hotspot usually works.

## Troubleshooting

### Cloudflared won't connect
- Check logs: `docker compose logs cloudflared`
- Look for "control stream encountered a failure" — means QUIC (UDP) is blocked
- Some networks block the QUIC connections cloudflared needs
- Try a different network (phone hotspot works reliably)
- Consider upgrading to a [named tunnel](named-tunnel.md) which falls back to HTTP/2

### Tunnel URL is stale (DNS doesn't resolve)
- Run `make status-tunnel` — it checks DNS resolution and HTTP liveness
- `docker compose restart` reuses the same container — cloudflared reconnects but doesn't always get a new URL
- `make tunnel` does `--force-recreate` which destroys and recreates the container, forcing a new quick tunnel registration
- Debug: `docker compose logs cloudflared --tail 20` — look for "Your quick Tunnel has been created" with a URL. If you only see "Registered tunnel connection" without a URL line, the container needs recreating

### Element shows "config.json not found" or wrong homeserver
- Run `make element-configure` to re-copy configs into `element/`
- For the hosted (Pages) Element, check that `make publish` ran after the last tunnel restart
- Run `make status-pages` to see what `config.json` is deployed with

### GitHub Pages shows README instead of Element
- Pages build type is `legacy` instead of `workflow`
- Run `make gh-setup` to switch, then push to trigger the workflow
- Verify with `make status-pages`

### Docker permission denied
- Add yourself to the docker group: `sudo usermod -aG docker $USER`
- Log out and back in (or use `sg docker -c "make up"` for current session)
