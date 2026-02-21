"""Status checks — docker, localhost, tunnel, GitHub Pages.

Ported from scripts/status.py.
"""

import json
import re
import socket
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

TUNNEL_URL_FILE = Path(__file__).parent.parent / "runtime" / "tunnel-url"


def _run(cmd: list[str] | str, timeout: int = 10, shell: bool = False) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd, shell=shell, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            cmd, returncode=1, stdout="", stderr=f"Command timed out after {timeout}s"
        )


def http_check(url: str, timeout: int = 5, verbose: bool = True) -> dict:
    result = {"url": url, "status": None, "headers": {}, "body": "", "error": None}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "frederick-matrix-status/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["status"] = resp.status
            result["headers"] = dict(resp.headers)
            result["body"] = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["headers"] = dict(e.headers)
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)

    if verbose:
        print(f"  GET {url}")
        if result["status"]:
            print(f"  HTTP {result['status']}")
        if result["body"]:
            body = result["body"]
            if len(body) > 500:
                body = body[:500] + f"... ({len(result['body'])} bytes total)"
            print(f"  Body: {body}")
        if result["error"]:
            print(f"  ERROR: {result['error']}")
    else:
        status = result["status"] or "UNREACHABLE"
        error = f" ({result['error']})" if result["error"] else ""
        print(f"  {url} -> {status}{error}")

    return result


def _section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def check_docker(verbose: bool = True) -> None:
    _section("Docker")

    print("--- Containers ---")
    r = _run(["docker", "compose", "ps"])
    print(r.stdout)
    if r.stderr:
        print(r.stderr)

    if verbose:
        print("--- Images ---")
        r = _run(["docker", "compose", "images"])
        print(r.stdout)

        print("--- Recent cloudflared logs (last 10) ---")
        r = _run(["docker", "compose", "logs", "cloudflared", "--tail", "10"])
        print(r.stdout)
        if r.stderr:
            print(r.stderr)


def check_localhost(verbose: bool = True) -> None:
    _section("Localhost")

    print("--- Synapse (http://localhost:8008) ---")
    result = http_check("http://localhost:8008/_matrix/client/versions", verbose=verbose)
    if result["body"] and not result["error"]:
        try:
            data = json.loads(result["body"])
            versions = data.get("versions", [])
            print(f"  Synapse spec versions: {len(versions)} ({versions[0]} .. {versions[-1]})")
            if verbose:
                features = data.get("unstable_features", {})
                enabled = [k for k, v in features.items() if v]
                print(f"  Enabled unstable features: {', '.join(enabled)}")
        except (json.JSONDecodeError, IndexError):
            pass

    print()
    print("--- Element (http://localhost:8080) ---")
    result = http_check("http://localhost:8080", verbose=verbose)
    if result["status"] == 200:
        print("  Element is being served by nginx")

    if verbose:
        print()
        print("--- Element config.json ---")
        result = http_check("http://localhost:8080/config.json", verbose=verbose)
        if result["body"] and not result["error"]:
            try:
                config = json.loads(result["body"])
                hs = config.get("default_server_config", {}).get("m.homeserver", {})
                print(f"  Configured homeserver: {hs.get('base_url', 'NOT SET')}")
                print(f"  Server name: {hs.get('server_name', 'NOT SET')}")
                print(f"  Brand: {config.get('brand', 'NOT SET')}")
            except json.JSONDecodeError:
                pass


def get_tunnel_url() -> str | None:
    """Read tunnel URL from runtime/tunnel-url file."""
    try:
        content = TUNNEL_URL_FILE.read_text().strip()
        return content if content else None
    except FileNotFoundError:
        return None


def check_tunnel(verbose: bool = True) -> None:
    _section("Cloudflare Tunnel")

    url = get_tunnel_url()
    if not url:
        print("  No tunnel URL found in runtime/tunnel-url.")
        print("  Is cloudflared running? Check: docker compose logs cloudflared")
        return

    print(f"  Tunnel URL: {url}")
    print()

    hostname = url.replace("https://", "").replace("http://", "")
    print(f"--- DNS resolve: {hostname} ---")
    try:
        ips = socket.getaddrinfo(hostname, 443)
        unique_ips = set(addr[4][0] for addr in ips)
        print(f"  Resolved to: {', '.join(unique_ips)}")
    except socket.gaierror as e:
        print(f"  DNS FAILED: {e}")
        print("  Tunnel URL is stale — run: ./manage.py tunnel restart")
        return

    print()
    print(f"--- {url}/_matrix/client/versions ---")
    result = http_check(f"{url}/_matrix/client/versions", verbose=verbose)
    if result["status"] == 200:
        print("  Tunnel is LIVE — Synapse is reachable from the internet")
    elif result["error"]:
        print("  Tunnel is UNREACHABLE — URL resolves but connection failed")


def get_github_pages_base() -> str | None:
    r = _run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
    if r.returncode != 0 or not r.stdout.strip():
        return None
    owner, repo = r.stdout.strip().split("/")
    return f"https://{owner}.github.io/{repo}"


def check_pages(verbose: bool = True) -> None:
    _section("GitHub Pages")

    base = get_github_pages_base()
    if not base:
        print("  Could not detect repo. Is `gh` authenticated?")
        return

    print(f"  Pages base: {base}")

    if verbose:
        print("--- Latest Pages deployment ---")
        r = _run([
            "gh", "run", "list",
            "--workflow=deploy-pages.yml",
            "--limit", "1",
            "--json", "status,conclusion,createdAt,displayTitle",
        ])
        if r.stdout.strip():
            try:
                runs = json.loads(r.stdout)
                if runs:
                    run = runs[0]
                    print(f"  {run.get('displayTitle', '?')}")
                    print(f"  Status: {run.get('status', '?')} / {run.get('conclusion', '?')}")
                    print(f"  Created: {run.get('createdAt', '?')}")
            except json.JSONDecodeError:
                print(f"  {r.stdout.strip()}")
        print()

    endpoints = [
        (f"{base}/", "Element Web"),
        (f"{base}/config.json", "Element config"),
        (f"{base}/server.json", "Server discovery"),
        (f"{base}/peers.json", "Peer discovery"),
        (f"{base}/home.html", "Mesh status page"),
    ]

    for url, label in endpoints:
        print(f"--- {label}: {url} ---")
        result = http_check(url, verbose=verbose)
        if result["body"] and not result["error"] and url.endswith(".json"):
            try:
                data = json.loads(result["body"])
                if "url" in data:
                    print(f"  Published tunnel URL: {data['url']}")
                    print(f"  Node name: {data.get('name', '?')}")
                if "peers" in data:
                    peers = data["peers"]
                    print(f"  Peer count: {len(peers)}")
                    for p in peers:
                        print(f"    - {p}")
                if "default_server_config" in data:
                    hs = data.get("default_server_config", {}).get("m.homeserver", {})
                    print(f"  Configured homeserver: {hs.get('base_url', 'NOT SET')}")
            except json.JSONDecodeError:
                pass
        print()


def cmd_status(args) -> None:
    """Run requested status checks."""
    checks = {
        "docker": check_docker,
        "localhost": check_localhost,
        "tunnel": check_tunnel,
        "pages": check_pages,
    }

    sections_arg = getattr(args, "section", None)
    if sections_arg:
        sections = [sections_arg]
    else:
        sections = list(checks.keys())

    verbose = not getattr(args, "quiet", False)

    for section in sections:
        if section not in checks:
            import sys
            print(f"Unknown section: {section}. Choose from: {', '.join(checks)}", file=sys.stderr)
            sys.exit(1)
        checks[section](verbose=verbose)
