# Matrix Mesh Chat

A self-hosted Matrix chat system for a small mesh of friends. Each member runs their own Synapse homeserver with an ephemeral Cloudflare tunnel. A shared Element Web client is hosted on GitHub Pages.

## Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) (not Docker Desktop)
- [GitHub CLI](https://cli.github.com/) (`gh auth login`)
- Python 3 with `requests` (`pip install requests`)
- Your user in the `docker` group: `sudo usermod -aG docker $USER` (log out/in after)

## Quick Start

```bash
make setup    # downloads Element, generates Synapse config, creates admin user
make start    # starts services and publishes tunnel URL to GitHub Pages
```

After setup:
- **Element**: http://localhost:8080
- **Synapse API**: http://localhost:8008
- **Tunnel**: printed by `make start` (changes each restart)

## How It Works

Each mesh member forks this repo and runs their own Synapse server. On startup, `start.sh`:

1. Starts Synapse, Element (nginx), and a Cloudflare quick tunnel
2. Detects the ephemeral `trycloudflare.com` URL
3. Publishes it to `element/server.json` on the repo's GitHub Pages via `gh api`

Peers discover each other through `peers.json`, which lists URLs to each peer's `server.json`. The Element home page fetches all peers and shows online/offline status.

## Day-to-Day

```bash
make start     # start + publish tunnel URL
make up        # start without publishing
make down      # stop
make logs      # follow logs
make status    # check if services are running
```

## Inviting People

Use the mesh-admin CLI to create invite tokens:

```bash
# First time: configure with your admin access token
# (get token from Element: Settings > Help & About > Access Token)
python3 mesh-admin/mesh_admin.py configure

# Create and manage invite tokens
make create-token           # single-use, expires in 7 days
make list-tokens            # show all tokens

# Or use the CLI directly for more options
python3 mesh-admin/mesh_admin.py create-token --uses 5 --expires 30d
python3 mesh-admin/mesh_admin.py revoke-token <token>
```

## Adding a Peer

1. Peer forks this repo, runs `make setup && make start`
2. Add their `server.json` URL to your `peers.json`:
   ```json
   {
     "peers": [
       "https://alice.github.io/matrix-mesh/element/server.json"
     ]
   }
   ```
3. They add yours to their `peers.json`
4. Both update `federation_domain_whitelist` in `data/homeserver.yaml`

## File Structure

```
├── Makefile                  # setup and management commands
├── start.sh                  # start services + publish tunnel URL
├── docker-compose.yml        # Synapse + nginx + cloudflared
├── data/                     # Synapse data (gitignored)
├── element/                  # Element Web (assets gitignored, configs tracked)
│   ├── config.json           # local dev config (localhost)
│   ├── config.prod.json      # production config template
│   ├── home.html             # mesh status landing page
│   ├── server.json           # this node's name + tunnel URL (updated by start.sh)
│   └── peers.json            # URLs to peers' server.json files
└── mesh-admin/
    └── mesh_admin.py         # registration token CLI
```
