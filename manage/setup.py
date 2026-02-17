"""Setup subcommand — first-time setup logic.

Ported from the Makefile setup targets.
"""

import subprocess
import sys
from pathlib import Path

ELEMENT_VERSION = "v1.12.10"
REPO_ROOT = Path(__file__).parent.parent


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, **kwargs)


def _run_or_die(args: list[str], desc: str) -> None:
    print(f"  {desc}...")
    result = _run(args)
    if result.returncode != 0:
        print(f"ERROR: {desc} failed", file=sys.stderr)
        sys.exit(result.returncode)


def element_download() -> None:
    element_dir = REPO_ROOT / "element"
    if (element_dir / "index.html").exists():
        print("  Element already downloaded, skipping.")
        return
    element_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://github.com/element-hq/element-web/releases/download/{ELEMENT_VERSION}/element-{ELEMENT_VERSION}.tar.gz"
    print(f"  Downloading Element {ELEMENT_VERSION}...")
    result = subprocess.run(
        f"curl -L {url} | tar xz --strip-components=1 -C element",
        shell=True,
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print("ERROR: Element download failed", file=sys.stderr)
        sys.exit(result.returncode)


def element_configure() -> None:
    print("  Copying element-config/ and discovery files into element/...")
    for src in (REPO_ROOT / "element-config").iterdir():
        dest = REPO_ROOT / "element" / src.name
        dest.write_bytes(src.read_bytes())
    for fname in ("server.json", "peers.json"):
        src = REPO_ROOT / fname
        if src.exists():
            (REPO_ROOT / "element" / fname).write_bytes(src.read_bytes())


def synapse_generate() -> None:
    homeserver_yaml = REPO_ROOT / "data" / "homeserver.yaml"
    if homeserver_yaml.exists():
        print("  Synapse config already exists, skipping.")
        return
    _run_or_die(
        [
            "docker", "compose", "run", "--rm",
            "-e", "SYNAPSE_SERVER_NAME=localhost",
            "-e", "SYNAPSE_REPORT_STATS=no",
            "synapse", "generate",
        ],
        "docker compose run synapse generate",
    )


def synapse_configure() -> None:
    homeserver_yaml = REPO_ROOT / "data" / "homeserver.yaml"
    if not homeserver_yaml.exists():
        print("ERROR: Run `./manage.py setup` or `synapse generate` first.", file=sys.stderr)
        sys.exit(1)

    content = homeserver_yaml.read_text()
    if "enable_registration:" in content:
        print("  Synapse already configured, skipping.")
        return

    additions = [
        "",
        "enable_registration: true",
        "enable_registration_without_verification: true",
        "",
        "auto_join_rooms:",
        '  - "#tech-frederick:localhost"',
        '  - "#general:localhost"',
        '  - "#random:localhost"',
        "auto_join_rooms_for_guests: false",
    ]
    homeserver_yaml.write_text(content + "\n".join(additions) + "\n")
    print("  Synapse configured.")


def admin_user() -> None:
    """Create the admin user. Requires services to be running."""
    import time, urllib.request, urllib.error

    print("  Waiting for Synapse to be ready...")
    for attempt in range(1, 11):
        try:
            urllib.request.urlopen(
                "http://localhost:8008/_matrix/client/versions", timeout=2
            )
            break
        except Exception:
            print(f"    attempt {attempt}...")
            time.sleep(2)
    else:
        print("ERROR: Synapse did not become ready in time.", file=sys.stderr)
        sys.exit(1)

    _run_or_die(
        [
            "docker", "compose", "exec", "synapse",
            "register_new_matrix_user",
            "-c", "/data/homeserver.yaml",
            "-a", "-u", "admin", "-p", "admin",
            "http://localhost:8008",
        ],
        "register admin user",
    )


def gh_setup() -> None:
    """Enable GitHub Pages with workflow-based deployment."""
    result = _run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("ERROR: `gh repo view` failed.", file=sys.stderr)
        sys.exit(1)
    repo = result.stdout.strip()
    print(f"  Repo: {repo}")

    pages_payload = '{"build_type":"workflow","source":{"branch":"main","path":"/"}}'

    print("  Attempting to create Pages site (may fail if already exists)...")
    _run(
        ["gh", "api", "-X", "POST", f"repos/{repo}/pages", "--input", "-"],
        input=pages_payload, text=True,
    )

    print("  Switching to workflow-based deployment...")
    result = _run(
        ["gh", "api", "-X", "PUT", f"repos/{repo}/pages", "--input", "-"],
        input=pages_payload, text=True, capture_output=True,
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    result = _run(
        ["gh", "api", f"repos/{repo}/pages", "--jq", ".build_type"],
        capture_output=True, text=True,
    )
    print(f"  Build type: {result.stdout.strip()}")
    print("  GitHub Pages enabled (workflow).")


def cmd_setup(args) -> None:
    """Run full first-time setup."""
    steps = [
        ("Downloading Element", element_download),
        ("Configuring Element", element_configure),
        ("Generating Synapse config", synapse_generate),
        ("Configuring Synapse", synapse_configure),
        ("Setting up GitHub Pages", gh_setup),
    ]

    for label, fn in steps:
        print(f"\n[{label}]")
        fn()

    print("\nSetup complete.")
    print("Next steps:")
    print("  ./manage.py up          # start services")
    print("  ./manage.py token configure   # set up admin credentials for token management")
    print("  ./manage.py status      # check everything is healthy")
