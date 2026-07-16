# Deployment

## Local / single-host (this project's primary target)

`docker-compose.yml` runs both services:

```bash
cp .env.example .env   # fill in API_KEYS, OPENAI_API_KEY (and/or ANTHROPIC_API_KEY)
make docker-up
```

- `backend` — FastAPI on `:8000`. `backend_data` volume persists the SQLite DB;
  `backend_indices` persists the FAISS index so it survives container restarts.
- `frontend` — static build served via `serve` on `:3000`, built with `VITE_API_BASE_URL`/
  `VITE_API_KEY` baked in at build time (Vite env vars are compile-time, not runtime — a
  different backend URL means a rebuild, not just a new env var at container start).

After the first `docker compose up`, build the interaction index once inside the container:

```bash
docker compose exec backend python -m scripts.build_interaction_index
```

## Secrets handling

`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `API_KEYS` are supplied via `.env` (gitignored,
never committed) for local/compose use. In any managed environment (ECS, Cloud Run, a PaaS),
these should come from that platform's secrets manager, not a checked-in or baked-in file.

## The single-writer SQLite constraint

This project runs one backend process against one SQLite file. That's sufficient for a
demo/single-tenant deployment but is the first thing to change before scaling horizontally:
SQLite serializes writes at the file level, and the in-process progress broadcaster
(`docs/api-architecture.md`) only reaches WebSocket clients connected to the same process. A
multi-replica deployment would need Postgres (or similar) plus a shared pub/sub (Redis) for
progress events.

## TLS termination

Neither Dockerfile terminates TLS — that's expected to happen at a reverse proxy or load
balancer in front of the containers (nginx, Caddy, an ALB, etc.), not in the application
containers themselves.

## CI

`.github/workflows/ci.yml` runs on every push/PR: backend (ruff, mypy, pytest) and frontend
(tsc, eslint, vitest, vite build) as independent jobs.

## Minimal non-Docker path

Both services can also run directly on a host with Python 3.11+ and Node 20+ — see the
Quickstart section of the root README. Useful for local development without Docker, or as
the basis for a systemd-unit or bare-VM deployment.
