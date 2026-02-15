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
make logs               Follow container logs
make status             Check if Synapse and Element are reachable
```

### Tunnel Management

```
make tunnel             Restart cloudflared for a new URL, publish to GitHub
make tunnel-url         Print the current tunnel URL (no restart)
make publish            Push current tunnel URL to server.json on GitHub
```

The tunnel URL is ephemeral — it changes every time cloudflared restarts. `make publish` pushes the new URL to GitHub, which triggers a Pages rebuild so peers and the hosted Element always have the latest URL.

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

Restarts only cloudflared, waits for the new URL, publishes it.

### "My tunnel URL is stale on GitHub Pages"

```bash
make publish
```

Re-reads the current tunnel URL from cloudflared logs and pushes to GitHub.

### "I want to invite someone"

```bash
# Create a token
make create-token

# Or for an unlimited token
python3 mesh-admin/mesh_admin.py create-token --uses 0

# Share:
# 1. The token
# 2. Your tunnel URL (make tunnel-url) or GitHub Pages link
```

### "A peer can't connect to me"

1. Check your tunnel: `make tunnel-url`
2. Check if it's reachable: `curl -s <tunnel-url>/_matrix/client/versions`
3. If not, restart the tunnel: `make tunnel`
4. Check your network — some restrictive networks (e.g., coffee shop WiFi with client isolation) block cloudflared's outbound connections. A phone hotspot usually works.

## Troubleshooting

### Cloudflared won't connect
- Check logs: `docker compose logs cloudflared`
- Some networks block the QUIC/HTTP2 connections cloudflared needs
- Try a different network (phone hotspot works reliably)

### Element shows "config.json not found" or wrong homeserver
- Run `make element-configure` to re-copy configs into `element/`
- For the hosted (Pages) Element, check that `make publish` ran after the last tunnel restart

### GitHub Pages shows README instead of Element
- Pages build type is `legacy` instead of `workflow`
- Run `make gh-setup` to switch, then push to trigger the workflow

### Docker permission denied
- Add yourself to the docker group: `sudo usermod -aG docker $USER`
- Log out and back in (or use `sg docker -c "make up"` for current session)
