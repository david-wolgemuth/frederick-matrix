ELEMENT_VERSION := v1.12.10

.PHONY: help setup element-download element-configure synapse-generate synapse-configure admin-user gh-setup start up down logs status create-token list-tokens

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup: element-download element-configure synapse-generate synapse-configure admin-user ## Full first-time setup

element-download: ## Download Element Web into element/
	@if [ -f element/index.html ]; then echo "Element already downloaded, skipping."; exit 0; fi
	mkdir -p element
	curl -L https://github.com/element-hq/element-web/releases/download/$(ELEMENT_VERSION)/element-$(ELEMENT_VERSION).tar.gz \
		| tar xz --strip-components=1 -C element

element-configure: ## Copy config files into element/
	cp element-config/* element/

synapse-generate: ## Generate Synapse config (only if data/ doesn't exist)
	@if [ -f data/homeserver.yaml ]; then echo "Synapse config already exists, skipping."; exit 0; fi
	docker compose run --rm \
		-e SYNAPSE_SERVER_NAME=localhost \
		-e SYNAPSE_REPORT_STATS=no \
		synapse generate

synapse-configure: ## Enable registration and auto-join rooms in homeserver.yaml
	@if [ ! -f data/homeserver.yaml ]; then echo "Run 'make synapse-generate' first."; exit 1; fi
	@if grep -q 'enable_registration:' data/homeserver.yaml; then echo "Already configured, skipping."; exit 0; fi
	@echo '' >> data/homeserver.yaml
	@echo 'enable_registration: true' >> data/homeserver.yaml
	@echo 'enable_registration_without_verification: true' >> data/homeserver.yaml
	@echo '' >> data/homeserver.yaml
	@echo 'auto_join_rooms:' >> data/homeserver.yaml
	@echo '  - "#tech-frederick:localhost"' >> data/homeserver.yaml
	@echo '  - "#general:localhost"' >> data/homeserver.yaml
	@echo '  - "#random:localhost"' >> data/homeserver.yaml
	@echo 'auto_join_rooms_for_guests: false' >> data/homeserver.yaml

admin-user: up ## Create admin user (starts server if needed)
	@echo "Waiting for Synapse to be ready..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		curl -sf http://localhost:8008/_matrix/client/versions > /dev/null 2>&1 && break; \
		sleep 2; \
	done
	docker compose exec synapse register_new_matrix_user \
		-c /data/homeserver.yaml -a -u admin -p admin http://localhost:8008

gh-setup: ## Enable GitHub Pages on the repo
	gh api -X POST "repos/$$(gh repo view --json nameWithOwner -q .nameWithOwner)/pages" \
		--input - <<< '{"source":{"branch":"main","path":"/"}}'
	@echo "GitHub Pages enabled."

start: ## Start services and publish tunnel URL to GitHub Pages
	./start.sh

up: ## Start Synapse, Element, and tunnel
	docker compose up -d

down: ## Stop everything
	docker compose down

logs: ## Follow container logs
	docker compose logs -f

status: ## Check server status
	@curl -sf http://localhost:8008/_matrix/client/versions > /dev/null 2>&1 \
		&& echo "Synapse:  up (http://localhost:8008)" \
		|| echo "Synapse:  down"
	@curl -sf http://localhost:8080 > /dev/null 2>&1 \
		&& echo "Element:  up (http://localhost:8080)" \
		|| echo "Element:  down"

create-token: ## Create a registration invite token
	python3 mesh-admin/mesh_admin.py create-token --expires 7d

list-tokens: ## List registration tokens
	python3 mesh-admin/mesh_admin.py list-tokens
