.PHONY: backend-install backend-dev backend-test backend-lint backend-typecheck \
        build-index init-db frontend-install frontend-dev frontend-test \
        frontend-typecheck frontend-lint frontend-build docker-up docker-down

backend-install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r requirements-dev.txt

init-db:
	cd backend && . .venv/bin/activate && python3 -c "import asyncio; from app.db.session import init_db; asyncio.run(init_db())"

build-index:
	cd backend && . .venv/bin/activate && python3 -m scripts.build_interaction_index

backend-dev:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

backend-test:
	cd backend && . .venv/bin/activate && python3 -m pytest tests -q

backend-lint:
	cd backend && . .venv/bin/activate && ruff check app scripts tests

backend-typecheck:
	cd backend && . .venv/bin/activate && mypy app scripts

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-test:
	cd frontend && npm test

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-lint:
	cd frontend && npm run lint

frontend-build:
	cd frontend && npm run build

docker-up:
	docker compose up --build

docker-down:
	docker compose down
