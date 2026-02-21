# Refactor: Unified `manage.py` CLI

## Welcome

This is a meaningful refactor of how frederick-matrix starts up, manages services, and handles tunnel publishing. You're consolidating scattered bash scripts, a Makefile with too much logic, and two separate Python CLIs into one clean system. The end result will be simpler to understand, easier to extend, and more aligned with how docker compose already works.

You've got this. The pieces are all here already — it's mostly reorganization with one new compose service.

---

## Why

Right now the same things can be done multiple ways:

- `make start` and `make up` do almost the same thing via different paths
- `start.sh` is a bash script doing polling, URL detection, and GitHub publishing — all things better handled in Python
- `scripts/status.py` and `mesh-admin/mesh_admin.py` are two separate CLI tools that should be subcommands of one tool
- The Makefile contains multi-line bash logic (for loops, conditionals) that belongs in Python

The guiding principles:

1. **Makefile** — thin aliases only, one-liners calling `./manage.py`
2. **`manage.py`** — unified Python CLI for anything more complex than a one-liner
3. **`docker-compose.yml`** — background processes are compose services, not detached bash loops

---

## The Target CLI

```
./manage.py setup                          # element download + synapse generate + configure + admin user + gh-setup
./manage.py up [-d]                        # docker compose up, wait for tunnel, publish. -d = detached
./manage.py down                           # docker compose down
./manage.py status [section] [-q]          # replaces scripts/status.py
./manage.py tunnel restart                 # force-recreate cloudflared, wait, publish
./manage.py tunnel url                     # print + check current tunnel URL
./manage.py publish                        # one-shot publish current URL to GitHub Pages
./manage.py token create [--uses N] [--expires 7d]
./manage.py token list [--active]
./manage.py token revoke <token>
./manage.py token configure
```

---

## Architecture Changes

### New Compose Service: `tunnel-watcher`

Currently `start.sh` runs a bash polling loop in the foreground to detect tunnel URL changes and publish them to GitHub Pages. This becomes a proper compose service.

**How it works:**

1. `manage.py up` grabs the GitHub auth token from the host via `gh auth token` (so users don't need to create PATs)
2. It passes `GITHUB_TOKEN`, `GITHUB_REPO`, and `NODE_NAME` as env vars to docker compose
3. The `tunnel-watcher` service uses these to publish `server.json` via the GitHub Contents API using `requests`

**How the watcher gets the tunnel URL:**

Cloudflared writes the URL to stdout. Rather than parsing docker logs or mounting the docker socket (security concern), we use a **shared volume with a wrapper entrypoint**:

```yaml
cloudflared:
  image: cloudflare/cloudflared:latest
  container_name: cloudflared
  volumes:
    - ./runtime:/runtime
  entrypoint: ["/bin/sh", "-c"]
  command:
    - |
      cloudflared tunnel --no-autoupdate --url http://synapse:8008 2>&1 \
        | tee /dev/stderr \
        | grep --line-buffered -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' \
        | while read url; do echo "$url" > /runtime/tunnel-url; done
  depends_on:
    - synapse
  restart: unless-stopped
```

The watcher service mounts the same volume:

```yaml
tunnel-watcher:
  build: ./tunnel-watcher
  container_name: tunnel-watcher
  volumes:
    - ./runtime:/runtime:ro
  environment:
    - GITHUB_TOKEN=${GITHUB_TOKEN}
    - GITHUB_REPO=${GITHUB_REPO}
    - NODE_NAME=${NODE_NAME}
    - POLL_INTERVAL=${POLL_INTERVAL:-60}
  depends_on:
    - cloudflared
  restart: unless-stopped
```

Key points:
- `runtime/` is gitignored
- `runtime/tunnel-url` is a plain text file anyone can `cat` — fully transparent
- No docker socket mount needed
- The watcher container is a tiny Python script with just `requests`

### `manage.py` Startup Flow

`./manage.py up`:

1. Run `gh auth token` → capture token
2. Run `gh repo view --json nameWithOwner` → extract repo and node name
3. Set `GITHUB_TOKEN`, `GITHUB_REPO`, `NODE_NAME` as env vars
4. Run `docker compose up -d`
5. Wait for `runtime/tunnel-url` to appear (poll the file)
6. Print status (Synapse URL, Element URL, tunnel URL)

`./manage.py up -d` is the same thing — the `-d` distinction from before goes away because the watcher is now a compose service. Both are detached. (You could still offer `-d` to skip the "wait and print status" step if you want, but it's optional.)

### What Gets Deleted

- `start.sh` — replaced by `manage.py up` + `tunnel-watcher` service
- `scripts/status.py` — absorbed into `manage.py status`
- `mesh-admin/mesh_admin.py` — absorbed into `manage.py token`

### Makefile After Refactor

The Makefile becomes nothing but aliases:

```makefile
.PHONY: help setup up down status logs create-token list-tokens

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup:        ## Full first-time setup
	./manage.py setup

up:           ## Start services, publish tunnel URL, watch for changes
	./manage.py up

down:         ## Stop everything
	./manage.py down

status:       ## Full status check
	./manage.py status

logs:         ## Follow container logs
	docker compose logs -f

create-token: ## Create a registration invite token (7 day expiry)
	./manage.py token create --expires 7d

list-tokens:  ## List registration tokens
	./manage.py token list
```

---

## File Structure After Refactor

```
frederick-matrix/
├── manage.py                 # unified CLI (executable, #!/usr/bin/env python3)
├── manage/                   # package directory for manage.py internals
│   ├── __init__.py
│   ├── setup.py              # setup subcommand logic
│   ├── compose.py            # up/down, env var injection, tunnel URL waiting
│   ├── status.py             # status checks (moved from scripts/status.py)
│   ├── tunnel.py             # tunnel restart, url check, publish
│   └── tokens.py             # token CRUD (moved from mesh-admin/mesh_admin.py)
├── tunnel-watcher/
│   ├── Dockerfile            # python:3.12-slim, pip install requests, copy watcher.py
│   └── watcher.py            # polls /runtime/tunnel-url, PUTs to GitHub API
├── runtime/                  # gitignored, shared volume
│   └── tunnel-url            # written by cloudflared entrypoint
├── Makefile                  # thin aliases only
├── docker-compose.yml        # 4 services: synapse, element, cloudflared, tunnel-watcher
├── server.json               # this node's identity (updated by tunnel-watcher)
├── peers.json                # peer discovery URLs
├── data/                     # synapse data (gitignored)
├── element/                  # element web assets (gitignored)
├── element-config/           # config templates
└── docs/                     # documentation
```

---

## Implementation Order

Work in this order so you always have something functional:

### Phase 1: Shared Volume + Cloudflared Entrypoint
- Add `runtime/` to `.gitignore`
- Update cloudflared service in `docker-compose.yml` with the entrypoint wrapper that writes to `/runtime/tunnel-url`
- Test: `docker compose up cloudflared`, confirm `runtime/tunnel-url` gets written
- This is the foundation everything else depends on

### Phase 2: Tunnel Watcher Service
- Create `tunnel-watcher/Dockerfile` and `tunnel-watcher/watcher.py`
- The watcher reads `/runtime/tunnel-url`, compares to last known, PUTs to GitHub API on change
- Add to `docker-compose.yml` with env var placeholders
- Test: set env vars manually, `docker compose up tunnel-watcher`, confirm it publishes

### Phase 3: `manage.py` Skeleton
- Create `manage.py` with argparse, subcommands stubbed out
- Implement `up` first — grab gh token, set env vars, `docker compose up -d`, wait for `runtime/tunnel-url`, print status
- Implement `down` — trivial, just `docker compose down`
- Test: `./manage.py up` and `./manage.py down` work end to end

### Phase 4: Absorb Existing CLIs
- Move `scripts/status.py` logic into `manage/status.py`, wire up `./manage.py status`
- Move `mesh-admin/mesh_admin.py` logic into `manage/tokens.py`, wire up `./manage.py token`
- Move setup logic from Makefile into `manage/setup.py`, wire up `./manage.py setup`
- Implement `./manage.py tunnel restart` and `./manage.py tunnel url`
- Implement `./manage.py publish` as a one-shot publish (useful for manual overrides)

### Phase 5: Slim the Makefile
- Replace all Makefile targets with one-line aliases to `./manage.py`
- Delete `start.sh`, `scripts/status.py`, `mesh-admin/mesh_admin.py`
- Update README and docs

---

## Key Design Decisions (and Why)

**Why not a docker socket mount for the watcher?**
Mounting `/var/run/docker.sock` gives a container full control over the host's Docker daemon. That's a significant security escalation for a project designed to be run by friends on personal machines. The shared file approach is simpler, safer, and more transparent.

**Why grab the GitHub token from `gh auth token` instead of asking for a PAT?**
This project is designed for people who already have `gh` installed and authenticated. Making them also create and manage a PAT is unnecessary friction. `gh auth token` gives us what we need with zero extra setup.

**Why keep the watcher as a compose service instead of a foreground loop in `manage.py`?**
Background processes should be compose services. If the host reboots or the user closes their terminal, the watcher keeps running (with `restart: unless-stopped`). It follows the same lifecycle as the other services — `docker compose down` stops everything cleanly.

**Why `manage.py` and not a branded CLI name?**
Follows Django convention. The repo name (`frederick-matrix`) already provides branding. No need to install anything on PATH or confuse the namespace.

**Why argparse and not Click?**
Fewer dependencies. This project deliberately keeps the Python dependency surface small (`requests` is the only non-stdlib dep on the host side). argparse is fine for this scope.

---

## Notes

- The `manage/` package modules should use `subprocess.run()` for docker/gh commands rather than shell=True bash strings where possible. Typed args, explicit error handling.
- `manage.py` should be `chmod +x` with a `#!/usr/bin/env python3` shebang.
- The tunnel-watcher Dockerfile should be minimal: `python:3.12-slim`, install `requests`, copy `watcher.py`, done.
- The watcher should log clearly — when it starts, when it detects a URL, when it publishes, when it encounters errors. Verbose output is preferred over silent operation.

---

## Questions? Stuck?

Look at the existing code for reference — `scripts/status.py` is well-structured and shows good patterns for the status checks. `mesh-admin/mesh_admin.py` has clean argparse subcommand setup. `start.sh` has all the publish logic you'll need to port to Python.

The hardest part is Phase 1 (the cloudflared entrypoint wrapper) because it's the thing you can't easily test without running the full stack. Get that working first and everything else flows from it.

