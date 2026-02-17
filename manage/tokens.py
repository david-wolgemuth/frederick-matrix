"""Token management — Synapse registration tokens.

Ported from mesh-admin/mesh_admin.py.
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

CONFIG_PATH = Path.home() / ".mesh-admin.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"No config found at {CONFIG_PATH}", file=sys.stderr)
        print("Run: ./manage.py token configure", file=sys.stderr)
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text())


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    CONFIG_PATH.chmod(0o600)


def synapse_request(method: str, endpoint: str, config: dict, body: dict | None = None) -> dict:
    url = config["server_url"].rstrip("/") + endpoint
    headers = {
        "Authorization": f"Bearer {config['access_token']}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            err = json.loads(raw)
            msg = err.get("error", raw)
        except Exception:
            msg = raw
        print(f"Error ({e.code}): {msg}", file=sys.stderr)
        sys.exit(1)


def parse_duration(duration_str: str) -> int:
    """Parse e.g. '7d', '1h', '2w' → expiry timestamp in milliseconds."""
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


def cmd_token(args) -> None:
    """Dispatch token subcommands."""
    subcmd = args.token_cmd
    dispatch = {
        "create": _token_create,
        "list": _token_list,
        "revoke": _token_revoke,
        "configure": _token_configure,
    }
    if subcmd not in dispatch:
        print(f"Unknown token subcommand: {subcmd}", file=sys.stderr)
        sys.exit(1)
    dispatch[subcmd](args)


def _token_configure(args) -> None:
    config = {}
    config["server_url"] = (
        getattr(args, "server", None)
        or input("Synapse server URL [http://localhost:8008]: ").strip()
        or "http://localhost:8008"
    )
    config["element_url"] = (
        getattr(args, "element", None)
        or input("Element URL [http://localhost:8080]: ").strip()
        or "http://localhost:8080"
    )
    config["access_token"] = (
        getattr(args, "token_value", None)
        or input("Admin access token: ").strip()
    )
    if not config["access_token"]:
        print("Access token is required.", file=sys.stderr)
        sys.exit(1)
    save_config(config)
    print(f"Config saved to {CONFIG_PATH}")


def _token_create(args) -> None:
    config = load_config()
    body: dict = {"length": 16}

    uses = getattr(args, "uses", None)
    if uses is not None:
        body["uses_allowed"] = uses if uses > 0 else None
    else:
        body["uses_allowed"] = 1

    expires = getattr(args, "expires", None)
    if expires:
        body["expiry_time"] = parse_duration(expires)

    token_data = synapse_request(
        "POST", "/_synapse/admin/v1/registration_tokens/new", config, body=body
    )

    print(f"Token:   {token_data['token']}")
    uses_val = token_data.get("uses_allowed")
    print(f"Uses:    {'unlimited' if uses_val is None else uses_val}")
    expiry = token_data.get("expiry_time")
    if expiry:
        print(f"Expires: {datetime.fromtimestamp(expiry / 1000).isoformat()}")
    else:
        print("Expires: never")
    element_url = config.get("element_url", "http://localhost:8080")
    print(f"Register: {element_url}/#/register")


def _token_list(args) -> None:
    config = load_config()
    data = synapse_request("GET", "/_synapse/admin/v1/registration_tokens", config)
    tokens = data.get("registration_tokens", [])

    if not tokens:
        print("No registration tokens.")
        return

    now_ms = int(datetime.now().timestamp() * 1000)
    active_only = getattr(args, "active", False)
    rows = []

    for t in tokens:
        uses_allowed = t.get("uses_allowed")
        completed = t.get("completed", 0)
        expiry = t.get("expiry_time")

        if expiry and expiry < now_ms:
            status = "expired"
        elif uses_allowed is not None and completed >= uses_allowed:
            status = "exhausted"
        else:
            status = "active"

        if active_only and status != "active":
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


def _token_revoke(args) -> None:
    config = load_config()
    token = args.token_value
    confirm = input(f"Revoke token {token}? [y/N] ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    synapse_request(
        "DELETE", f"/_synapse/admin/v1/registration_tokens/{token}", config
    )
    print(f"Token {token} revoked.")
