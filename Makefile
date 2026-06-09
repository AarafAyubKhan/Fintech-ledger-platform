# ============================================
# FinSight AI — Makefile
# ============================================

.PHONY: help dev stop build test lint clean setup

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------- Setup ----------
setup: ## Initial project setup
	cp -n .env.example .env || true
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

# ---------- Development ----------
dev: ## Start all services (Docker Compose)
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

dev-backend: ## Start backend only
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend only
	cd frontend && npm run dev

dev-infra: ## Start infrastructure only (DB, Redis, Qdrant)
	docker compose up postgres redis qdrant minio -d

stop: ## Stop all services
	docker compose down

# ---------- Database ----------
db-migrate: ## Create new migration
	cd backend && alembic revision --autogenerate -m "$(msg)"

db-upgrade: ## Apply migrations
	cd backend && alembic upgrade head

db-downgrade: ## Rollback last migration
	cd backend && alembic downgrade -1

db-reset: ## Reset database
	cd backend && alembic downgrade base && alembic upgrade head

# ---------- Testing ----------
test: ## Run all tests
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing
	cd frontend && npm test

test-backend: ## Run backend tests only
	cd backend && pytest tests/ -v --cov=app --cov-report=html

test-frontend: ## Run frontend tests only
	cd frontend && npm test

test-e2e: ## Run end-to-end tests
	cd frontend && npx playwright test

# ---------- Code Quality ----------
lint: ## Lint all code
	cd backend && ruff check app/ tests/
	cd frontend && npm run lint

format: ## Format all code
	cd backend && ruff format app/ tests/
	cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

type-check: ## Type check
	cd backend && mypy app/
	cd frontend && npx tsc --noEmit

# ---------- Build ----------
build: ## Build production Docker images
	docker compose build

build-backend: ## Build backend Docker image
	docker build -t finsight-backend -f infra/docker/backend.Dockerfile .

build-frontend: ## Build frontend Docker image
	docker build -t finsight-frontend -f infra/docker/frontend.Dockerfile .

# ---------- Data ----------
seed: ## Seed sample data
	cd backend && python -m scripts.seed_sample_data

ingest: ## Ingest sample documents
	cd backend && python -m scripts.ingest_documents

# ---------- Cleanup ----------
clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
