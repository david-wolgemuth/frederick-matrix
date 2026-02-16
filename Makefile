ELEMENT_VERSION := v1.12.10

.PHONY: help setup element-download element-configure synapse-generate synapse-configure admin-user gh-setup start up down logs status status-quick status-docker status-localhost status-tunnel status-pages tunnel tunnel-url publish create-token list-tokens

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup: element-download element-configure synapse-generate synapse-configure admin-user ## Full first-time setup

element-download: ## Download Element Web into element/
	@if [ -f element/index.html ]; then echo "Element already downloaded, skipping."; exit 0; fi
	mkdir -p element
	curl -L https://github.com/element-hq/element-web/releases/download/$(ELEMENT_VERSION)/element-$(ELEMENT_VERSION).tar.gz \
		| tar xz --strip-components=1 -C element

element-configure: ## Copy config and discovery files into element/
	cp element-config/* element/
	cp server.json peers.json element/

synapse-generate: ## Generate Synapse config (only if data/ doesn't exist)
	@if [ -f data/homeserver.yaml ]; then echo "Synapse config already exists, skipping."; exit 0; fi
	docker compose run --rm \
		-e SYNAPSE_SERVER_NAME=localhost \
		-e SYNAPSE_REPORT_STATS=no \
		synapse generate

synapse-configure: ## Enable registration and auto-join rooms in homeserver.yaml
	@if [ ! -f data/homeserver.yaml ]; then echo "Run 'make synapse-generate' first."; exit 1; fi
	@if grep -q 'enable_registration:' data/homeserver.yaml; then echo "Already configured, skipping."; exit 0; fi
	echo '' >> data/homeserver.yaml
	echo 'enable_registration: true' >> data/homeserver.yaml
	echo 'enable_registration_without_verification: true' >> data/homeserver.yaml
	echo '' >> data/homeserver.yaml
	echo 'auto_join_rooms:' >> data/homeserver.yaml
	echo '  - "#tech-frederick:localhost"' >> data/homeserver.yaml
	echo '  - "#general:localhost"' >> data/homeserver.yaml
	echo '  - "#random:localhost"' >> data/homeserver.yaml
	echo 'auto_join_rooms_for_guests: false' >> data/homeserver.yaml

admin-user: up ## Create admin user (starts server if needed)
	echo "Waiting for Synapse to be ready..."
	for i in 1 2 3 4 5 6 7 8 9 10; do \
		curl -sf http://localhost:8008/_matrix/client/versions > /dev/null 2>&1 && break; \
		echo "  attempt $$i ..."; \
		sleep 2; \
	done
	docker compose exec synapse register_new_matrix_user \
		-c /data/homeserver.yaml -a -u admin -p admin http://localhost:8008

gh-setup: ## Enable GitHub Pages (workflow-based deployment)
	REPO=$$(gh repo view --json nameWithOwner -q .nameWithOwner); \
	echo "Repo: $$REPO"; \
	echo "Attempting to create Pages site ..."; \
	echo '{"build_type":"workflow","source":{"branch":"main","path":"/"}}' \
		| gh api -X POST "repos/$$REPO/pages" --input - 2>&1 || true; \
	echo "Switching to workflow-based deployment ..."; \
	echo '{"build_type":"workflow","source":{"branch":"main","path":"/"}}' \
		| gh api -X PUT "repos/$$REPO/pages" --input -; \
	echo "Verifying ..."; \
	gh api "repos/$$REPO/pages" --jq '.build_type'; \
	echo "GitHub Pages enabled (workflow)."

start: ## Start services and publish tunnel URL to GitHub Pages
	./start.sh

up: ## Start services, wait for tunnel, publish URL to GitHub
	docker compose up -d
	echo "Waiting for tunnel URL..."
	for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do \
		URL=$$(docker compose logs cloudflared 2>&1 | grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | tail -1); \
		if [ -n "$$URL" ]; then echo "Tunnel: $$URL"; break; fi; \
		echo "  attempt $$i ..."; \
		sleep 2; \
	done
	$(MAKE) publish

down: ## Stop everything
	docker compose down

tunnel: ## Recreate tunnel for new URL and publish to GitHub
	docker compose up -d --force-recreate cloudflared
	echo "Waiting for new tunnel URL..."
	for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do \
		URL=$$(docker compose logs cloudflared 2>&1 | grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | tail -1); \
		if [ -n "$$URL" ]; then echo "Tunnel: $$URL"; break; fi; \
		echo "  attempt $$i ..."; \
		sleep 2; \
	done
	$(MAKE) publish

tunnel-url: ## Show current tunnel URL and check if live
	URL=$$(docker compose logs cloudflared 2>&1 | grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | tail -1); \
	if [ -z "$$URL" ]; then echo "No tunnel URL found in logs"; exit 1; fi; \
	echo "Tunnel URL: $$URL"; \
	LAST_SEEN=$$(docker compose logs --timestamps cloudflared 2>&1 | grep "$$URL" | tail -1 | grep -oP '^\S+'); \
	if [ -n "$$LAST_SEEN" ]; then echo "Last seen in logs: $$LAST_SEEN"; fi; \
	echo "Checking if tunnel is reachable ..."; \
	if curl -sf --max-time 5 "$$URL/_matrix/client/versions" > /dev/null 2>&1; then \
		echo "✓ LIVE - Tunnel is reachable"; \
	else \
		echo "✗ UNREACHABLE - URL may be stale (tunnel died or DNS expired)"; \
	fi

publish: ## Push current tunnel URL to server.json on GitHub
	set -e; \
	echo "--- Detecting repo ---"; \
	REPO=$$(gh repo view --json nameWithOwner -q .nameWithOwner); \
	echo "Repo: $$REPO"; \
	NODE_NAME=$$(echo "$$REPO" | cut -d/ -f1); \
	echo "Node name: $$NODE_NAME"; \
	echo "--- Detecting tunnel URL ---"; \
	URL=$$(docker compose logs cloudflared 2>&1 | grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | tail -1); \
	echo "Tunnel URL: $$URL"; \
	if [ -z "$$URL" ]; then echo "ERROR: No tunnel URL found. Is cloudflared running?"; exit 1; fi; \
	echo "--- Writing server.json ---"; \
	jq -n --arg name "$$NODE_NAME" --arg url "$$URL" '{name: $$name, url: $$url}' > server.json; \
	cat server.json; \
	echo "--- Pushing to GitHub ---"; \
	CONTENT=$$(base64 -w 0 < server.json); \
	echo "Base64 content length: $$(echo -n "$$CONTENT" | wc -c) chars"; \
	echo "Fetching current SHA for server.json ..."; \
	SHA=$$(gh api "repos/$$REPO/contents/server.json" 2>/dev/null | jq -r '.sha // ""'); \
	echo "Current SHA: $$SHA"; \
	if [ -n "$$SHA" ]; then \
		echo "Updating existing file ..."; \
		jq -n --arg msg "Update tunnel URL" --arg content "$$CONTENT" --arg sha "$$SHA" \
			'{message: $$msg, content: $$content, sha: $$sha}' \
			| gh api -X PUT "repos/$$REPO/contents/server.json" --input -; \
	else \
		echo "Creating new file ..."; \
		jq -n --arg msg "Update tunnel URL" --arg content "$$CONTENT" \
			'{message: $$msg, content: $$content}' \
			| gh api -X PUT "repos/$$REPO/contents/server.json" --input -; \
	fi; \
	echo "Published: $$URL"

logs: ## Follow container logs
	docker compose logs -f

status: ## Full status check: docker, localhost, tunnel, GitHub Pages
	python3 scripts/status.py

status-quick: ## Quick status summary
	python3 scripts/status.py -q

status-docker: ## Status: docker only
	python3 scripts/status.py docker

status-localhost: ## Status: localhost only
	python3 scripts/status.py localhost

status-tunnel: ## Status: tunnel only
	python3 scripts/status.py tunnel

status-pages: ## Status: GitHub Pages only
	python3 scripts/status.py pages

create-token: ## Create a registration invite token
	python3 mesh-admin/mesh_admin.py create-token --expires 7d

list-tokens: ## List registration tokens
	python3 mesh-admin/mesh_admin.py list-tokens
