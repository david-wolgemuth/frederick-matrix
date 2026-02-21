#!/usr/bin/env python3
"""Tunnel URL watcher — polls /runtime/tunnel-url and publishes to GitHub Pages.

Reads env vars:
  GITHUB_TOKEN   - GitHub token (from `gh auth token` on host)
  GITHUB_REPO    - full repo slug, e.g. "david-wolgemuth/frederick-matrix"
  NODE_NAME      - short name for this node, e.g. "david-wolgemuth"
  POLL_INTERVAL  - seconds between checks (default: 60)
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

import requests

logging.basicConfig(
    format="%(asctime)s [watcher] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

TUNNEL_URL_FILE = Path("/runtime/tunnel-url")


def get_env(key: str) -> str:
    val = os.environ.get(key, "").strip()
    if not val:
        log.error("Required env var %s is not set", key)
        sys.exit(1)
    return val


def read_tunnel_url() -> str | None:
    """Return the current tunnel URL from the shared volume file, or None."""
    try:
        content = TUNNEL_URL_FILE.read_text().strip()
        return content if content else None
    except FileNotFoundError:
        return None


def publish(url: str, github_token: str, github_repo: str, node_name: str) -> None:
    """PUT server.json to the GitHub Contents API."""
    api_base = f"https://api.github.com/repos/{github_repo}/contents/server.json"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    server_json = json.dumps({"name": node_name, "url": url}, indent=2) + "\n"
    import base64
    content_b64 = base64.b64encode(server_json.encode()).decode()

    # Fetch current SHA (needed for updates)
    sha = None
    resp = requests.get(api_base, headers=headers, timeout=10)
    if resp.ok:
        sha = resp.json().get("sha")

    payload: dict = {
        "message": "Update tunnel URL",
        "content": content_b64,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(api_base, headers=headers, json=payload, timeout=10)
    if resp.ok:
        log.info("Published: %s", url)
    else:
        log.error("GitHub API error %s: %s", resp.status_code, resp.text[:200])


def main() -> None:
    github_token = get_env("GITHUB_TOKEN")
    github_repo = get_env("GITHUB_REPO")
    node_name = get_env("NODE_NAME")
    poll_interval = int(os.environ.get("POLL_INTERVAL", "60"))

    log.info("Starting tunnel watcher (poll every %ss)", poll_interval)
    log.info("Repo: %s  Node: %s", github_repo, node_name)

    current_url: str | None = None

    while True:
        url = read_tunnel_url()

        if url and url != current_url:
            log.info("Detected tunnel URL: %s", url)
            try:
                publish(url, github_token, github_repo, node_name)
                current_url = url
            except Exception as exc:
                log.error("Publish failed: %s", exc)
        elif not url:
            log.debug("No tunnel URL yet, waiting...")

        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
