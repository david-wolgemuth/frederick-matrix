"""Compose helpers: up, down, env injection, tunnel URL waiting."""

import os
import subprocess
import sys
import time
from pathlib import Path

TUNNEL_URL_FILE = Path(__file__).parent.parent / "runtime" / "tunnel-url"
TUNNEL_WAIT_SECONDS = 120
TUNNEL_POLL_INTERVAL = 2


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, **kwargs)


def get_github_env() -> dict[str, str]:
    """Return GITHUB_TOKEN, GITHUB_REPO, NODE_NAME by running gh CLI."""
    token_result = _run(
        ["gh", "auth", "token"],
        capture_output=True, text=True,
    )
    if token_result.returncode != 0:
        print("ERROR: `gh auth token` failed. Are you authenticated with `gh auth login`?", file=sys.stderr)
        sys.exit(1)
    token = token_result.stdout.strip()

    repo_result = _run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True, text=True,
    )
    if repo_result.returncode != 0:
        print("ERROR: `gh repo view` failed. Are you in a GitHub-backed git repo?", file=sys.stderr)
        sys.exit(1)
    repo = repo_result.stdout.strip()
    node_name = repo.split("/")[0]

    return {
        "GITHUB_TOKEN": token,
        "GITHUB_REPO": repo,
        "NODE_NAME": node_name,
    }


def cmd_up(args) -> None:
    """Start services, wait for tunnel URL, print status."""
    print("Fetching GitHub credentials...")
    extra_env = get_github_env()
    print(f"  Repo: {extra_env['GITHUB_REPO']}")
    print(f"  Node: {extra_env['NODE_NAME']}")

    env = {**os.environ, **extra_env}

    print("Starting services...")
    result = _run(["docker", "compose", "up", "-d"], env=env)
    if result.returncode != 0:
        print("ERROR: docker compose up failed", file=sys.stderr)
        sys.exit(result.returncode)

    print(f"Waiting for tunnel URL (up to {TUNNEL_WAIT_SECONDS}s)...")
    url = _wait_for_tunnel_url()

    if not url:
        print(
            "ERROR: Tunnel URL not found after waiting.\n"
            "Check: docker compose logs cloudflared",
            file=sys.stderr,
        )
        sys.exit(1)

    print()
    print(f"  Synapse:  http://localhost:8008")
    print(f"  Element:  http://localhost:8080")
    print(f"  Tunnel:   {url}")
    print()
    print("tunnel-watcher is running and will re-publish if the URL changes.")


def cmd_down(args) -> None:
    """Stop all services."""
    result = _run(["docker", "compose", "down"])
    sys.exit(result.returncode)


def _wait_for_tunnel_url() -> str | None:
    """Poll runtime/tunnel-url file until it contains a URL or timeout."""
    deadline = time.time() + TUNNEL_WAIT_SECONDS
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        if TUNNEL_URL_FILE.exists():
            content = TUNNEL_URL_FILE.read_text().strip()
            if content:
                return content
        print(f"  attempt {attempt}...")
        time.sleep(TUNNEL_POLL_INTERVAL)
    return None
