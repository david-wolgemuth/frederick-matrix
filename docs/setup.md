# Setup Guide

## Prerequisites

- **Docker Engine** (not Docker Desktop): https://docs.docker.com/engine/install/
- **GitHub CLI**: https://cli.github.com/ — run `gh auth login`
- **Python 3** with `requests`: `pip install requests`
- **jq**: `sudo apt install jq` (used by `make publish`)
- Your user in the `docker` group: `sudo usermod -aG docker $USER` (log out/in after)

## First-Time Setup

```bash
# 1. Fork and clone
gh repo fork david-wolgemuth/frederick-matrix --clone
cd frederick-matrix

# 2. Run setup (downloads Element, generates Synapse config, creates admin user)
make setup

# 3. Enable GitHub Pages with workflow deployment
make gh-setup

# 4. Start services and publish tunnel URL
make up
```

### What `make setup` Does

1. **`element-download`** — Downloads Element Web v1.12.10 into `element/`
2. **`element-configure`** — Copies config files and discovery files into `element/`
3. **`synapse-generate`** — Generates `data/homeserver.yaml` via Docker
4. **`synapse-configure`** — Enables open registration and auto-join rooms
5. **`admin-user`** — Creates admin user (`admin`/`admin`)

### What `make gh-setup` Does

Switches GitHub Pages from legacy "deploy from branch" to workflow-based deployment. This is required for the GitHub Actions workflow to deploy Element Web.

## Verify It Works

```bash
# Check services
make status

# Check tunnel URL
make tunnel-url

# Check GitHub Pages deployment
gh run list --limit 1
```

After `make up`:
- **Element (local)**: http://localhost:8080
- **Synapse API**: http://localhost:8008
- **Tunnel**: printed in output (random `trycloudflare.com` URL)
- **GitHub Pages**: `https://<you>.github.io/frederick-matrix/`

## Configure mesh-admin

The admin CLI needs an access token to manage registration tokens.

```bash
# Get your access token from Element:
#   Settings > Help & About > Access Token (at bottom)

python3 mesh-admin/mesh_admin.py configure \
  --server http://localhost:8008 \
  --element http://localhost:8080 \
  --token "syt_YOUR_TOKEN_HERE"
```

Config saved to `~/.mesh-admin.json` (chmod 600).

## Adding Peers

1. Your peer forks the repo, runs setup, and starts their node
2. Add their `server.json` URL to your `peers.json`:

```json
{
  "peers": [
    "https://their-username.github.io/frederick-matrix/server.json"
  ]
}
```

3. Commit and push — the workflow redeploys with the updated peer list
4. They add your URL to their `peers.json`

## Inviting Users

```bash
# Create a single-use token expiring in 7 days (default)
make create-token

# Create an unlimited-use token that never expires
python3 mesh-admin/mesh_admin.py create-token --uses 0

# List all tokens
make list-tokens
```

Share the token + your tunnel URL (or GitHub Pages link) with the person you're inviting.
