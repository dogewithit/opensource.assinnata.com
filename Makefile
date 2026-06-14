# opensource.assinnata.com — local dev & validation
#
# Every example must pass `make test` (run against LocalStack + Postgres) or it
# is rejected. See ROADMAP.md.

SHELL := /bin/bash
VENV  := .venv
PY    := $(VENV)/bin/python
PIP   := $(VENV)/bin/pip

.PHONY: help up down logs wait venv test test-% fmt frontend clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up: ## Start LocalStack 4.14 + Postgres
	docker compose up -d
	$(MAKE) wait

down: ## Stop and remove the local stack
	docker compose down -v

logs: ## Tail the local stack logs
	docker compose logs -f

wait: ## Block until LocalStack + Postgres are healthy
	@echo "waiting for services to become healthy..."
	@for i in $$(seq 1 40); do \
		ls_ok=$$(docker inspect -f '{{.State.Health.Status}}' oss-localstack 2>/dev/null || echo none); \
		pg_ok=$$(docker inspect -f '{{.State.Health.Status}}' oss-postgres 2>/dev/null || echo none); \
		if [ "$$ls_ok" = "healthy" ] && [ "$$pg_ok" = "healthy" ]; then echo "ready."; exit 0; fi; \
		sleep 2; \
	done; echo "services did not become healthy in time" >&2; exit 1

minikube-up: ## Start a local minikube cluster (profile oss) for the Kubernetes examples
	minikube start --driver=docker --cpus=4 --memory=4096 --profile=oss

minikube-down: ## Delete the minikube cluster
	minikube delete --profile=oss

venv: ## Create the shared Python venv and install all example deps
	@test -d $(VENV) || python3 -m venv $(VENV)
	@$(PIP) install -q --upgrade pip
	@for req in examples/*/requirements.txt; do \
		echo "installing $$req"; $(PIP) install -q -r $$req; \
	done

test: venv up ## Run every example's test suite against the local stack
	@set -e; for d in examples/*/; do \
		if [ -d "$$d/tests" ]; then \
			echo "=== testing $$d ==="; \
			$(PY) -m pytest "$$d/tests" -q || exit 1; \
		fi; \
	done; echo "ALL EXAMPLES PASSED"

test-%: venv up ## Run a single example's tests, e.g. `make test-hyperliquid-crawler`
	$(PY) -m pytest examples/$*/tests -q

frontend: ## Run the Astro frontend dev server
	cd frontend && npm install && npm run dev

clean: ## Remove venv and build artifacts
	rm -rf $(VENV) frontend/dist
