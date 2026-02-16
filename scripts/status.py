#!/usr/bin/env python3
"""frederick-matrix status checker.

Usage:
    ./scripts/status.py              # all checks
    ./scripts/status.py docker       # just docker
    ./scripts/status.py localhost    # just localhost
    ./scripts/status.py tunnel       # just tunnel
    ./scripts/status.py pages        # just github pages
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path


def run(cmd: str, timeout: int = 10) -> subprocess.CompletedProcess:
    """Run a shell command, capture output, never raise on failure."""
    try:
        return subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            cmd, returncode=1, stdout="", stderr=f"Command timed out after {timeout}s"
        )


def http_check(url: str, timeout: int = 5, verbose: bool = True) -> dict:
    """GET a URL, return {status, headers, body, error} dict. Uses urllib only."""
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
            for k, v in result["headers"].items():
                print(f"    {k}: {v}")
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


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def check_docker(verbose: bool = True) -> None:
    """Run docker compose ps, docker compose images, recent cloudflared logs."""
    print_section("Docker")

    print("--- Containers ---")
    result = run("docker compose ps")
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if verbose:
        print("--- Images ---")
        result = run("docker compose images")
        print(result.stdout)

        print("--- Recent cloudflared logs (last 10) ---")
        result = run("docker compose logs cloudflared --tail 10")
        print(result.stdout)
        if result.stderr:
            print(result.stderr)


def check_localhost(verbose: bool = True) -> None:
    """Check Synapse at :8008 and Element at :8080."""
    print_section("Localhost")

    print("--- Synapse (http://localhost:8008) ---")
    result = http_check(
        "http://localhost:8008/_matrix/client/versions",
        verbose=verbose,
    )
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
    """Extract most recent trycloudflare.com URL from cloudflared logs."""
    result = run("docker compose logs cloudflared 2>&1")
    urls = re.findall(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", result.stdout)
    return urls[-1] if urls else None


def check_tunnel(verbose: bool = True) -> None:
    """Resolve tunnel URL and hit /_matrix/client/versions."""
    print_section("Cloudflare Tunnel")

    url = get_tunnel_url()
    if not url:
        print("  No tunnel URL found in cloudflared logs.")
        print("  Is cloudflared running? Check: docker compose logs cloudflared")
        return

    print(f"  Tunnel URL (from logs): {url}")
    print()

    # DNS check
    import socket
    hostname = url.replace("https://", "")
    print(f"--- DNS resolve: {hostname} ---")
    try:
        ips = socket.getaddrinfo(hostname, 443)
        unique_ips = set(addr[4][0] for addr in ips)
        print(f"  Resolved to: {', '.join(unique_ips)}")
    except socket.gaierror as e:
        print(f"  DNS FAILED: {e}")
        print("  Tunnel URL is stale — cloudflared needs to establish a new connection.")
        return

    print()
    print(f"--- {url}/_matrix/client/versions ---")
    result = http_check(f"{url}/_matrix/client/versions", verbose=verbose)
    if result["status"] == 200:
        print("  Tunnel is LIVE — Synapse is reachable from the internet")
    elif result["error"]:
        print("  Tunnel is UNREACHABLE — URL resolves but connection failed")


def get_github_pages_base() -> str | None:
    """Derive https://<owner>.github.io/<repo> from gh CLI."""
    result = run("gh repo view --json nameWithOwner -q .nameWithOwner")
    if result.returncode != 0 or not result.stdout.strip():
        return None
    owner, repo = result.stdout.strip().split("/")
    return f"https://{owner}.github.io/{repo}"


def check_pages(verbose: bool = True) -> None:
    """Check Element, server.json, home.html on GitHub Pages."""
    print_section("GitHub Pages")

    base = get_github_pages_base()
    if not base:
        print("  Could not detect repo. Is `gh` authenticated?")
        return

    print(f"  Pages base: {base}")

    # Check Pages deployment config
    result = run("gh api repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/pages --jq '.build_type' 2>/dev/null")
    if result.stdout.strip():
        print(f"  Build type: {result.stdout.strip()}")
    print()

    # Check most recent workflow run
    if verbose:
        print("--- Latest Pages deployment ---")
        result = run("gh run list --workflow=deploy-pages.yml --limit 1 --json status,conclusion,createdAt,displayTitle")
        if result.stdout.strip():
            try:
                runs = json.loads(result.stdout)
                if runs:
                    r = runs[0]
                    print(f"  {r.get('displayTitle', '?')}")
                    print(f"  Status: {r.get('status', '?')} / {r.get('conclusion', '?')}")
                    print(f"  Created: {r.get('createdAt', '?')}")
            except json.JSONDecodeError:
                print(f"  {result.stdout.strip()}")
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

        # Parse JSON responses for extra info
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


def main() -> None:
    """Parse args and run requested checks."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "sections",
        nargs="*",
        default=[],
        help="Sections to check: docker, localhost, tunnel, pages (default: all)",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Summary only, no verbose output"
    )
    args = parser.parse_args()

    checks = {
        "docker": check_docker,
        "localhost": check_localhost,
        "tunnel": check_tunnel,
        "pages": check_pages,
    }

    sections = list(checks.keys()) if not args.sections or "all" in args.sections else args.sections
    for section in sections:
        checks[section](verbose=not args.quiet)


if __name__ == "__main__":
    main()
