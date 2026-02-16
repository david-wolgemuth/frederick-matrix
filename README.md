# Matrix Mesh Chat

A self-hosted Matrix chat system for a small mesh of friends. Each member runs their own Synapse homeserver with an ephemeral Cloudflare tunnel. Peers discover each other via GitHub Pages.

## Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) (not Docker Desktop)
- [GitHub CLI](https://cli.github.com/) (`gh auth login`)
- Python 3 with `requests` (`pip install requests`)
- Your user in the `docker` group: `sudo usermod -aG docker $USER` (log out/in after)

## Quick Start

```bash
# 1. Fork/clone this repo, push to your GitHub
# 2. First-time setup
make setup        # downloads Element, generates Synapse config, creates admin user
make gh-setup     # enables GitHub Pages on your repo

# 3. Edit peers.json to add your peers' server.json URLs
# 4. Start everything
make start        # starts services, publishes tunnel URL, watches for changes
```

After setup:
- **Element**: http://localhost:8080
- **Synapse API**: http://localhost:8008
- **Tunnel**: printed by `make start` (changes each restart)

## How It Works

Each mesh member runs their own Synapse. On startup, `start.sh`:

1. Starts Synapse, Element (nginx), and a Cloudflare quick tunnel
2. Detects the ephemeral `trycloudflare.com` URL
3. Publishes it to `server.json` on the repo's GitHub Pages via `gh api`
4. Watches for tunnel URL changes and re-publishes automatically

Peers discover each other through `peers.json`, which lists URLs to each peer's `server.json` on their GitHub Pages. The Element home page fetches all peers and shows online/offline status.

## Day-to-Day

```bash
make up        # start services, publish tunnel URL to GitHub
make down      # stop
make tunnel    # restart tunnel for a new URL, publish
make tunnel-url # print current tunnel URL
make publish   # re-publish current URL to GitHub
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

1. Peer forks this repo, pushes to their GitHub
2. Runs `make setup && make gh-setup && make start`
3. Add their `server.json` URL to your `peers.json`:
   ```json
   {
     "peers": [
       "https://alice.github.io/matrix-mesh/server.json"
     ]
   }
   ```
4. They add yours to their `peers.json`

## Documentation

- **[Quickstart Guide](docs/quickstart.md)** — Step-by-step getting started
- **[Architecture](docs/architecture.md)** — System design and data flow
- **[Setup Guide](docs/setup.md)** — Detailed setup instructions
- **[Operations](docs/operations.md)** — Day-to-day commands and troubleshooting
- **[Named Tunnel Setup](docs/named-tunnel.md)** — Upgrade to stable Cloudflare tunnel
- **[Networking Guide](docs/networking.md)** — Port forwarding and network configuration

## File Structure

```
├── Makefile                  # setup and management commands
├── start.sh                  # start services + publish/watch tunnel URL
├── docker-compose.yml        # Synapse + nginx + cloudflared
├── server.json               # this node's name + tunnel URL (updated by make publish)
├── peers.json                # URLs to peers' server.json files
├── data/                     # Synapse data (gitignored)
├── element/                  # Element Web assets (gitignored, downloaded at setup)
├── element-config/           # Config files copied into element/ at setup
│   ├── config.json           # local dev config (localhost)
│   ├── config.prod.json      # production config template
│   └── home.html             # mesh status landing page
├── scripts/
│   └── status.py             # status checker (make status)
├── mesh-admin/
│   └── mesh_admin.py         # registration token CLI
└── docs/                     # documentation
    ├── quickstart.md          # step-by-step getting started
    ├── architecture.md        # system design and data flow
    ├── operations.md          # day-to-day commands and troubleshooting
    ├── setup.md               # detailed setup guide
    ├── named-tunnel.md        # named Cloudflare tunnel upgrade
    └── networking.md          # port forwarding and network guides
```
