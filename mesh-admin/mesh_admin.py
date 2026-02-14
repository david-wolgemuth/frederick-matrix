"""Mesh Admin CLI - manage Synapse registration tokens for your Matrix mesh."""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

CONFIG_PATH = Path.home() / ".mesh-admin.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"No config found at {CONFIG_PATH}")
        print("Run: mesh-admin configure")
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text())


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    CONFIG_PATH.chmod(0o600)


def synapse_request(method: str, endpoint: str, config: dict, **kwargs) -> requests.Response:
    url = config["server_url"].rstrip("/") + endpoint
    headers = {"Authorization": f"Bearer {config['access_token']}"}
    resp = requests.request(method, url, headers=headers, **kwargs)
    if not resp.ok:
        try:
            err = resp.json()
            msg = err.get("error", resp.text)
        except Exception:
            msg = resp.text
        print(f"Error ({resp.status_code}): {msg}", file=sys.stderr)
        sys.exit(1)
    return resp


def parse_duration(duration_str: str) -> int:
    units = {"h": "hours", "d": "days", "w": "weeks"}
    suffix = duration_str[-1]
    if suffix not in units:
        print(f"Unknown duration unit '{suffix}'. Use h, d, or w.", file=sys.stderr)
        sys.exit(1)
    try:
        value = int(duration_str[:-1])
    except ValueError:
        print(f"Invalid duration: {duration_str}", file=sys.stderr)
        sys.exit(1)
    expiry = datetime.now() + timedelta(**{units[suffix]: value})
    return int(expiry.timestamp() * 1000)


def cmd_configure(args: argparse.Namespace) -> None:
    config = {}
    config["server_url"] = args.server or input("Synapse server URL [http://localhost:8008]: ").strip() or "http://localhost:8008"
    config["element_url"] = args.element or input("Element URL [http://localhost:8080]: ").strip() or "http://localhost:8080"
    config["access_token"] = args.token or input("Admin access token: ").strip()
    if not config["access_token"]:
        print("Access token is required.", file=sys.stderr)
        sys.exit(1)
    save_config(config)
    print(f"Config saved to {CONFIG_PATH}")


def cmd_create_token(args: argparse.Namespace) -> None:
    config = load_config()
    body = {"length": 16}
    if args.uses is not None:
        body["uses_allowed"] = args.uses if args.uses > 0 else None
    else:
        body["uses_allowed"] = 1
    if args.expires:
        body["expiry_time"] = parse_duration(args.expires)

    resp = synapse_request("POST", "/_synapse/admin/v1/registration_tokens/new", config, json=body)
    token_data = resp.json()

    print(f"Token:   {token_data['token']}")
    uses = token_data.get("uses_allowed")
    print(f"Uses:    {'unlimited' if uses is None else uses}")
    expiry = token_data.get("expiry_time")
    if expiry:
        print(f"Expires: {datetime.fromtimestamp(expiry / 1000).isoformat()}")
    else:
        print("Expires: never")
    element_url = config.get("element_url", "http://localhost:8080")
    print(f"Register: {element_url}/#/register")


def cmd_list_tokens(args: argparse.Namespace) -> None:
    config = load_config()
    resp = synapse_request("GET", "/_synapse/admin/v1/registration_tokens", config)
    tokens = resp.json().get("registration_tokens", [])

    if not tokens:
        print("No registration tokens.")
        return

    now_ms = int(datetime.now().timestamp() * 1000)
    rows = []
    for t in tokens:
        uses_allowed = t.get("uses_allowed")
        completed = t.get("completed", 0)
        pending = t.get("pending", 0)
        expiry = t.get("expiry_time")

        if expiry and expiry < now_ms:
            status = "expired"
        elif uses_allowed is not None and completed >= uses_allowed:
            status = "exhausted"
        else:
            status = "active"

        if args.active and status != "active":
            continue

        token_display = t["token"][:8] + "..."
        uses_display = f"{completed}/{uses_allowed}" if uses_allowed is not None else f"{completed}/unlimited"
        expiry_display = datetime.fromtimestamp(expiry / 1000).strftime("%Y-%m-%d %H:%M") if expiry else "-"

        rows.append((token_display, uses_display, status, expiry_display))

    if not rows:
        print("No matching tokens.")
        return

    print(f"{'TOKEN':<14} {'USES':<14} {'STATUS':<12} {'EXPIRES'}")
    for token, uses, status, expiry in rows:
        print(f"{token:<14} {uses:<14} {status:<12} {expiry}")


def cmd_revoke_token(args: argparse.Namespace) -> None:
    config = load_config()
    confirm = input(f"Revoke token {args.token}? [y/N] ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    synapse_request("DELETE", f"/_synapse/admin/v1/registration_tokens/{args.token}", config)
    print(f"Token {args.token} revoked.")


def main():
    parser = argparse.ArgumentParser(prog="mesh-admin", description="Manage Synapse registration tokens for your Matrix mesh.")
    sub = parser.add_subparsers(dest="command")

    p_configure = sub.add_parser("configure", help="Set up admin credentials")
    p_configure.add_argument("--server", help="Synapse server URL")
    p_configure.add_argument("--element", help="Element Web URL")
    p_configure.add_argument("--token", help="Admin access token")
    p_configure.set_defaults(func=cmd_configure)

    p_create = sub.add_parser("create-token", help="Create a registration token")
    p_create.add_argument("--uses", type=int, help="Number of uses (0 = unlimited, default: 1)")
    p_create.add_argument("--expires", help="Expiry duration (e.g. 1h, 7d, 4w)")
    p_create.set_defaults(func=cmd_create_token)

    p_list = sub.add_parser("list-tokens", help="List registration tokens")
    p_list.add_argument("--active", action="store_true", help="Only show active tokens")
    p_list.set_defaults(func=cmd_list_tokens)

    p_revoke = sub.add_parser("revoke-token", help="Revoke a registration token")
    p_revoke.add_argument("token", help="Token to revoke")
    p_revoke.set_defaults(func=cmd_revoke_token)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
