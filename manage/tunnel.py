"""Tunnel management: restart, url, publish."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

TUNNEL_URL_FILE = Path(__file__).parent.parent / "runtime" / "tunnel-url"
TUNNEL_WAIT_SECONDS = 60
TUNNEL_POLL_INTERVAL = 2


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, **kwargs)


def _read_tunnel_url() -> str | None:
    """Read current URL from runtime/tunnel-url file."""
    try:
        content = TUNNEL_URL_FILE.read_text().strip()
        return content if content else None
    except FileNotFoundError:
        return None


def _wait_for_new_url(previous: str | None) -> str | None:
    """Wait for a URL that is different from `previous`."""
    deadline = time.time() + TUNNEL_WAIT_SECONDS
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        url = _read_tunnel_url()
        if url and url != previous:
            return url
        print(f"  attempt {attempt}...")
        time.sleep(TUNNEL_POLL_INTERVAL)
    return None


def cmd_tunnel(args) -> None:
    """Dispatch tunnel subcommands."""
    if args.tunnel_cmd == "restart":
        _tunnel_restart(args)
    elif args.tunnel_cmd == "url":
        _tunnel_url(args)
    else:
        print(f"Unknown tunnel subcommand: {args.tunnel_cmd}", file=sys.stderr)
        sys.exit(1)


def _tunnel_restart(args) -> None:
    """Force-recreate cloudflared and wait for new URL."""
    old_url = _read_tunnel_url()

    # Clear the file so we don't read a stale URL
    if TUNNEL_URL_FILE.exists():
        TUNNEL_URL_FILE.write_text("")

    print("Restarting cloudflared...")
    result = _run(["docker", "compose", "up", "-d", "--force-recreate", "cloudflared"])
    if result.returncode != 0:
        print("ERROR: docker compose up --force-recreate cloudflared failed", file=sys.stderr)
        sys.exit(result.returncode)

    print(f"Waiting for new tunnel URL (up to {TUNNEL_WAIT_SECONDS}s)...")
    url = _wait_for_new_url(old_url)

    if not url:
        print("ERROR: No new tunnel URL detected. Check: docker compose logs cloudflared", file=sys.stderr)
        sys.exit(1)

    print(f"New tunnel URL: {url}")
    print("tunnel-watcher will publish the new URL automatically.")


def _tunnel_url(args) -> None:
    """Print current tunnel URL and check reachability."""
    import urllib.request
    import urllib.error
    import socket

    url = _read_tunnel_url()
    if not url:
        print("No tunnel URL found in runtime/tunnel-url.", file=sys.stderr)
        print("Is cloudflared running? Check: docker compose logs cloudflared", file=sys.stderr)
        sys.exit(1)

    print(f"Tunnel URL: {url}")

    hostname = url.replace("https://", "").replace("http://", "")
    print(f"\nDNS resolve: {hostname}")
    try:
        ips = socket.getaddrinfo(hostname, 443)
        unique_ips = set(addr[4][0] for addr in ips)
        print(f"  Resolved to: {', '.join(unique_ips)}")
    except socket.gaierror as e:
        print(f"  DNS FAILED: {e}")
        print("  Tunnel URL is stale — restart with: ./manage.py tunnel restart")
        sys.exit(1)

    print(f"\nChecking reachability: {url}/_matrix/client/versions")
    try:
        req = urllib.request.Request(
            f"{url}/_matrix/client/versions",
            headers={"User-Agent": "manage.py/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"  HTTP {resp.status} — LIVE")
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} — reachable but error")
    except Exception as e:
        print(f"  UNREACHABLE: {e}")
        sys.exit(1)


def cmd_publish(args) -> None:
    """One-shot: read tunnel URL and publish to GitHub Pages."""
    from manage.compose import get_github_env

    url = _read_tunnel_url()
    if not url:
        print("ERROR: No tunnel URL found in runtime/tunnel-url.", file=sys.stderr)
        print("Is cloudflared running?", file=sys.stderr)
        sys.exit(1)

    print(f"Tunnel URL: {url}")

    env = get_github_env()
    github_token = env["GITHUB_TOKEN"]
    github_repo = env["GITHUB_REPO"]
    node_name = env["NODE_NAME"]

    _publish_url(url, github_token, github_repo, node_name)


def _publish_url(url: str, github_token: str, github_repo: str, node_name: str) -> None:
    """Write server.json locally and PUT to GitHub Contents API."""
    import base64
    import urllib.request
    import urllib.error

    repo_root = Path(__file__).parent.parent
    server_json_path = repo_root / "server.json"

    data = {"name": node_name, "url": url}
    content_str = json.dumps(data, indent=2) + "\n"

    # Write locally
    server_json_path.write_text(content_str)
    print(f"Wrote server.json: {content_str.strip()}")

    # Push to GitHub API
    content_b64 = base64.b64encode(content_str.encode()).decode()
    api_url = f"https://api.github.com/repos/{github_repo}/contents/server.json"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }

    # Fetch existing SHA
    sha = None
    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            existing = json.loads(resp.read().decode())
            sha = existing.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"WARNING: Could not fetch existing server.json SHA: {e}", file=sys.stderr)

    payload: dict = {"message": "Update tunnel URL", "content": content_b64}
    if sha:
        payload["sha"] = sha

    import urllib.parse
    body = json.dumps(payload).encode()
    req = urllib.request.Request(api_url, data=body, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"Published to GitHub: {url}")
    except urllib.error.HTTPError as e:
        print(f"ERROR: GitHub API returned {e.code}: {e.read().decode()[:200]}", file=sys.stderr)
        sys.exit(1)
