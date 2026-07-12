.PHONY: help backend-install backend-dev backend-test backend-lint backend-typecheck \
	init-db build-index seed-claims \
	frontend-install frontend-dev frontend-build frontend-typecheck frontend-lint frontend-test \
	docker-up docker-down

help:
	@echo "Backend:"
	@echo "  make backend-install     Install backend deps (editable, with dev extras)"
	@echo "  make backend-dev         Run the backend dev server (uvicorn --reload)"
	@echo "  make backend-test        Run backend test suite"
	@echo "  make backend-lint        Run ruff against the backend"
	@echo "  make backend-typecheck   Run mypy against the backend"
	@echo "  make init-db             Create database tables"
	@echo "  make build-index         Build the policy_corpus FAISS index"
	@echo "  make seed-claims         Generate synthetic historical claims"
	@echo ""
	@echo "Frontend:"
	@echo "  make frontend-install    Install frontend deps"
	@echo "  make frontend-dev        Run the frontend dev server"
	@echo "  make frontend-build      Production build the frontend"
	@echo "  make frontend-typecheck  Run tsc --noEmit"
	@echo "  make frontend-lint       Run eslint"
	@echo "  make frontend-test       Run the Vitest test suite"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up           Build and start both services via docker compose"
	@echo "  make docker-down         Stop docker compose services"

backend-install:
	cd backend && pip install -e ".[dev]"

backend-dev:
	cd backend && uvicorn app.main:app --reload

backend-test:
	cd backend && pytest

backend-lint:
	cd backend && ruff check app scripts tests

backend-typecheck:
	cd backend && mypy app scripts tests

init-db:
	cd backend && python -m scripts.init_db

build-index:
	cd backend && python -m scripts.build_policy_index

seed-claims:
	cd backend && python -m scripts.generate_synthetic_claims

frontend-install:
	cd frontend && npm ci

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npm test

docker-up:
	docker compose up --build

docker-down:
	docker compose down
