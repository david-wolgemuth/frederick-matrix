# Architecture

## Overview

Each mesh member runs three Docker services locally and publishes their ephemeral tunnel URL to GitHub Pages. Peers discover each other by fetching `server.json` from each other's Pages sites.

```
┌─────────────────────────────────────────────────┐
│ Your Machine (Docker Compose)                   │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Synapse  │  │ Element  │  │ Cloudflared  │  │
│  │ :8008    │  │ :8080    │  │ (quick tun.) │  │
│  └──────────┘  └──────────┘  └──────┬───────┘  │
│       │                             │           │
└───────┼─────────────────────────────┼───────────┘
        │                             │
        │ localhost                   │ https://*.trycloudflare.com
        ▼                             ▼
   Local Element              Internet (peers connect here)
```

## Services

### Synapse (`synapse`)
- Matrix homeserver (matrixdotorg/synapse)
- Runs as UID/GID 1000 to match host user
- Data stored in `data/` (gitignored)
- Port 8008

### Element Web (`element`)
- nginx:alpine serving static Element Web files
- Element downloaded at setup into `element/` (gitignored)
- Config files copied from `element-config/`
- Port 8080

### Cloudflare Tunnel (`cloudflared`)
- Proxies internet traffic to Synapse on port 8008
- **Quick tunnel** (default): no account needed, ephemeral URL changes every restart
- **Named tunnel** (recommended): free Cloudflare account, stable permanent URL, HTTP/2 fallback on restrictive networks
- See [Named Tunnel Setup](named-tunnel.md) and [Networking Guide](networking.md)

## Peer Discovery

```
┌──────────┐  make publish   ┌──────────────┐
│ Your     │ ──────────────► │ GitHub API   │
│ Machine  │  server.json    │ (contents)   │
└──────────┘                 └──────┬───────┘
                                    │ triggers
                                    ▼
                             ┌──────────────┐
                             │ GH Actions   │
                             │ Workflow      │
                             └──────┬───────┘
                                    │ deploys
                                    ▼
                             ┌──────────────┐
                             │ GitHub Pages │
                             │ server.json  │ ◄── peers fetch this
                             │ Element Web  │
                             │ home.html    │
                             └──────────────┘
```

1. `make up` starts services, waits for tunnel URL, runs `make publish`
2. `make publish` writes `server.json` (name + tunnel URL) to GitHub via API
3. The API commit triggers the GitHub Actions workflow
4. Workflow downloads Element Web, injects tunnel URL into `config.json`, deploys to Pages
5. Peers fetch your `server.json` from Pages to find your current URL

### Discovery Files

**`server.json`** — This node's identity (repo root, updated by `make publish`):
```json
{
  "name": "alice",
  "url": "https://random-words.trycloudflare.com"
}
```

**`peers.json`** — URLs to other members' `server.json` on their Pages:
```json
{
  "peers": [
    "https://bob.github.io/frederick-matrix/server.json"
  ]
}
```

## GitHub Pages

The workflow (`deploy-pages.yml`) builds a site containing:
- Element Web (downloaded from GitHub releases)
- `config.json` generated with current tunnel URL from `server.json`
- `home.html` mesh status page (shows self + peer status)
- `server.json` and `peers.json` for peer discovery

Pages must use **workflow-based deployment** (`make gh-setup`), not legacy "deploy from branch".

### Live URLs (per member)

| URL | Content |
|-----|---------|
| `https://<user>.github.io/frederick-matrix/` | Element Web app (login/chat) |
| `https://<user>.github.io/frederick-matrix/home.html` | Mesh status page (node health) |
| `https://<user>.github.io/frederick-matrix/server.json` | This node's name + current tunnel URL |
| `https://<user>.github.io/frederick-matrix/peers.json` | URLs to peer `server.json` files |
| `https://<user>.github.io/frederick-matrix/config.json` | Element config (generated at deploy, points to tunnel) |

The hosted Element at the Pages root is pre-configured to connect to the node's tunnel URL — no manual homeserver entry needed. The `home.html` status page is embedded in Element's home tab and also accessible standalone (with an "Open Element" link when viewed directly).

## Config Files

| File | Location | Purpose |
|------|----------|---------|
| `element-config/config.json` | Committed | Local dev config (points to `localhost:8008`) |
| `element-config/config.prod.json` | Committed | Template for production |
| `element-config/home.html` | Committed | Mesh status page source |
| `build/config.json` | CI only | Generated at deploy time with tunnel URL |

## Data Flow: User Registration

1. Admin creates invite token: `make create-token` (calls Synapse Admin API)
2. Admin shares token + their GitHub Pages link with friend
3. Friend opens hosted Element on GitHub Pages (already configured with the right homeserver)
4. Friend registers with the invite token
5. Auto-join rooms: `#tech-frederick:localhost`, `#general:localhost`, `#random:localhost`

Alternatively, friends can use any Element client and manually set the homeserver to the tunnel URL.
