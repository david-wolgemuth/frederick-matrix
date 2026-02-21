.PHONY: help setup up down status logs create-token list-tokens

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup: ## Full first-time setup
	./manage.py setup

up: ## Start services, publish tunnel URL, watch for changes
	./manage.py up

down: ## Stop everything
	./manage.py down

status: ## Full status check
	./manage.py status

logs: ## Follow container logs
	docker compose logs -f

create-token: ## Create a registration invite token (7 day expiry)
	./manage.py token create --expires 7d

list-tokens: ## List registration tokens
	./manage.py token list
