# Quickstart: Getting Up and Running

Step-by-step with verification at each stage.

## 1. Prerequisites

```bash
# Docker
docker --version          # Docker Engine 20+
docker compose version    # v2+

# GitHub CLI
gh auth status            # Must be logged in

# Python
python3 -c "import requests"   # Must have requests

# jq
jq --version              # Used by make publish
```

If any are missing, see [Setup Guide](setup.md#prerequisites).

## 2. Clone and Setup

```bash
git clone https://github.com/david-wolgemuth/frederick-matrix.git
cd frederick-matrix
make setup
```

**Verify:** Each step prints progress. If anything fails, it stops. Check with:
```bash
ls element/index.html         # Element downloaded?
ls data/homeserver.yaml       # Synapse config generated?
make status                   # Services running?
```

## 3. Check Localhost

```bash
make status
```

You should see:
```
=== Localhost ===
Synapse http://localhost:8008/_matrix/client/versions
{"versions":["r0.0.1","r0.1.0", ...]}
Element http://localhost:8080
  OK
```

Open http://localhost:8080 in your browser. You should see Element Web with the Matrix Mesh branding.

**Test login:** Use the admin account (`admin` / `admin`) or register a new account.

## 4. Enable GitHub Pages

```bash
make gh-setup
```

**Verify:**
```bash
# Push to trigger the workflow
git push

# Wait for deployment (~60s)
gh run list --limit 1

# Check it's live
make status
# Look at the "=== GitHub Pages ===" section
```

Open `https://<you>.github.io/frederick-matrix/` — should show Element Web.
Open `https://<you>.github.io/frederick-matrix/home.html` — should show the mesh status page.

## 5. Start the Tunnel

```bash
make up
```

This starts all services, waits for the Cloudflare tunnel URL, and publishes it to GitHub.

**Verify:**
```bash
make status
# Look at the "=== Cloudflare Tunnel ===" section
# Should show a trycloudflare.com URL and "OK" (not UNREACHABLE)
```

If the tunnel is UNREACHABLE, your network may be blocking QUIC. See [Networking Guide](networking.md). Try a phone hotspot, or upgrade to a [named tunnel](named-tunnel.md).

## 6. Test External Access

From another device (phone, different computer), open your tunnel URL:
```
https://random-words.trycloudflare.com
```

You should see the Synapse API response. Then try Element on GitHub Pages — it's pre-configured to connect to your tunnel.

## 7. Invite Someone

```bash
# Create an invite token
python3 mesh-admin/mesh_admin.py create-token --uses 0

# Share with them:
# 1. The token
# 2. Your GitHub Pages URL: https://<you>.github.io/frederick-matrix/
```

They open your Pages link, click register, enter the token, done. Auto-joins `#tech-frederick`, `#general`, `#random`.

## What `make status` Checks

`make status` runs `scripts/status.py` which performs verbose checks across four sections. Use `make status-quick` for a summary, or check individual sections with `make status-docker`, `make status-localhost`, `make status-tunnel`, `make status-pages`.

| Section | What it tests |
|---------|--------------|
| Docker | `docker compose ps`, images, recent cloudflared logs |
| Localhost | Synapse API (`localhost:8008`), Element (`localhost:8080`), Element `config.json` |
| Tunnel | Extracts URL from logs, DNS resolution, HTTP check via `/_matrix/client/versions` |
| Pages | Element, `config.json` (shows configured homeserver), `server.json`, `peers.json`, `home.html` |

## Troubleshooting by Status

**Docker containers not running:**
```bash
make up                    # Start them
docker compose logs        # Check for errors
```

**Localhost OK but tunnel UNREACHABLE:**
- Network blocking QUIC — try phone hotspot
- Tunnel URL stale — `make tunnel` to get a new one
- See [Networking Guide](networking.md)

**Tunnel URL stale (DNS doesn't resolve):**
- `make tunnel` (force-recreates cloudflared container for a fresh URL)
- A simple `docker compose restart` won't always get a new URL — `make tunnel` uses `--force-recreate`

**Tunnel OK but Pages UNREACHABLE:**
- Pages not enabled — `make gh-setup`
- Workflow hasn't run — `git push` to trigger
- Check workflow: `gh run list --limit 1`

**Pages shows stale tunnel URL:**
- Run `make publish` to push current URL
- Wait ~60s for Pages rebuild

**Everything OK but friend can't connect:**
- Share your GitHub Pages URL, not the tunnel URL directly
- Make sure they have the registration token
- Check their network can reach `*.trycloudflare.com`
