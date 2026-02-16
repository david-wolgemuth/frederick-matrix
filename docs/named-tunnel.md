# Named Cloudflare Tunnel (Recommended)

Quick tunnels (`trycloudflare.com`) are great for testing but have two problems:
- URL changes every restart — peers and Element config go stale
- QUIC-only — fails on restrictive networks (coffee shops, corporate WiFi)

Named tunnels fix both: **stable URL** that survives restarts, and **automatic HTTP/2 fallback** when QUIC is blocked.

Requires a free Cloudflare account.

## Setup

### 1. Create a Cloudflare account

Sign up at https://cloudflare.com (free tier is fine).

### 2. Login from your machine

```bash
cloudflared tunnel login
```

This opens a browser to authorize. Creates `~/.cloudflared/cert.pem`.

### 3. Create a named tunnel

```bash
cloudflared tunnel create frederick-matrix
```

This generates a credentials file at `~/.cloudflared/<tunnel-id>.json`. Note the tunnel ID.

### 4. Create tunnel config

Create `cloudflared/config.yml` in the repo:

```yaml
tunnel: frederick-matrix
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: frederick-matrix.yourdomain.com
    service: http://synapse:8008
  - service: http_status:404
```

If you don't have a custom domain, the tunnel is reachable at `<tunnel-id>.cfargotunnel.com`.

### 5. Add DNS record (if using custom domain)

```bash
cloudflared tunnel route dns frederick-matrix frederick-matrix.yourdomain.com
```

### 6. Update docker-compose.yml

Replace the quick tunnel cloudflared service:

```yaml
cloudflared:
  image: cloudflare/cloudflared:latest
  command: tunnel run frederick-matrix
  volumes:
    - ./cloudflared:/etc/cloudflared:ro
  depends_on:
    - synapse
  restart: unless-stopped
```

Copy your credentials into the repo (gitignored):

```bash
mkdir -p cloudflared
cp ~/.cloudflared/<tunnel-id>.json cloudflared/credentials.json
cp cloudflared/config.yml cloudflared/
```

### 7. Update .gitignore

```
cloudflared/credentials.json
```

The `config.yml` can be committed, but credentials must not be.

### 8. Update server.json

Since the URL is now permanent, set it once:

```json
{
  "name": "your-github-username",
  "url": "https://frederick-matrix.yourdomain.com"
}
```

Commit and push. No more `make publish` needed on every restart.

## Why Named Tunnels Work on Restrictive Networks

Quick tunnels use QUIC (UDP) exclusively. Many networks block or throttle UDP.

Named tunnels try QUIC first, then **automatically fall back to HTTP/2 (TCP)**. TCP port 443 is almost never blocked — it's regular HTTPS traffic.

## DuckDNS (Optional Backup)

If you ever move to a network where you can port-forward, DuckDNS gives you a free stable hostname pointing at your IP:

```yaml
duckdns:
  image: lscr.io/linuxserver/duckdns:latest
  environment:
    - SUBDOMAINS=frederick-matrix
    - TOKEN=your-duckdns-token
  restart: unless-stopped
```

Sign up at https://www.duckdns.org/ (free, up to 5 subdomains).

This is complementary — DuckDNS handles DNS, but you still need port forwarding. The Cloudflare tunnel doesn't require port forwarding at all.

## Quick Tunnel vs Named Tunnel

| | Quick Tunnel | Named Tunnel |
|---|---|---|
| Account required | No | Yes (free) |
| URL stability | New URL every restart | Permanent |
| Protocol fallback | QUIC only | QUIC → HTTP/2 |
| Port forwarding | Not needed | Not needed |
| Config complexity | Zero | One-time setup |
| Peer discovery | Needed (GitHub Pages) | Optional |
