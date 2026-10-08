# Suad AI — developer commands
.DEFAULT_GOAL := help
PY ?= python3
PIP ?= $(PY) -m pip
BACKEND := backend

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install minimal/core Python dependencies
	$(PIP) install -r requirements-core.txt

.PHONY: install-full
install-full: ## Install ALL dependencies incl. heavy providers
	$(PIP) install -r requirements.txt

.PHONY: dev
dev: ## Run the backend API with autoreload
	cd $(BACKEND) && $(PY) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: frontend
frontend: ## Run the React admin UI dev server
	cd frontend && npm install && npm run dev

.PHONY: test
test: ## Run the test suite
	$(PY) -m pytest -q

.PHONY: lint
lint: ## Lint with ruff
	$(PY) -m ruff check $(BACKEND) tests

.PHONY: format
format: ## Auto-format with ruff
	$(PY) -m ruff format $(BACKEND) tests
	$(PY) -m ruff check --fix $(BACKEND) tests

.PHONY: migrate
migrate: ## Apply database migrations (alembic upgrade head)
	$(PY) -m alembic -c alembic.ini upgrade head

.PHONY: makemigration
makemigration: ## Autogenerate a new migration: make makemigration m="message"
	$(PY) -m alembic -c alembic.ini revision --autogenerate -m "$(m)"

.PHONY: docker-up
docker-up: ## Start the full stack with Docker Compose
	docker compose up -d --build

.PHONY: docker-down
docker-down: ## Stop the Docker Compose stack
	docker compose down

.PHONY: seed
seed: ## Insert demo agent + permission roles
	cd $(BACKEND) && $(PY) -m app.scripts.seed
