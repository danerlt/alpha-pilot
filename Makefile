.PHONY: help dev-up dev-down dev-backend init-db upgrade-db test test-unit test-integration lint fmt

DOCKER_DEV = docker compose -f docker/docker-compose.dev.yml

help:
	@echo "AlphaPilot Development Commands"
	@echo ""
	@echo "  make dev-up          Start dev infrastructure (postgres, redis)"
	@echo "  make dev-down        Stop dev infrastructure"
	@echo "  make dev-backend     Start FastAPI backend (hot reload)"
	@echo "  make init-db         Initialize database schema"
	@echo "  make upgrade-db      Run pending Alembic migrations"
	@echo "  make test            Run all tests"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make lint            Run ruff linter"
	@echo "  make fmt             Run ruff formatter"

dev-up:
	$(DOCKER_DEV) up -d

dev-down:
	$(DOCKER_DEV) down

dev-backend:
	cd backend && source .venv/bin/activate && uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

init-db:
	cd backend && source .venv/bin/activate && python scripts/init_db.py

upgrade-db:
	cd backend && source .venv/bin/activate && python scripts/upgrade_db.py

test:
	cd backend && source .venv/bin/activate && pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	cd backend && source .venv/bin/activate && pytest tests/unit/ -v

test-integration:
	cd backend && source .venv/bin/activate && pytest tests/integration/ -v

lint:
	cd backend && source .venv/bin/activate && ruff check src/ tests/

fmt:
	cd backend && source .venv/bin/activate && ruff format src/ tests/
