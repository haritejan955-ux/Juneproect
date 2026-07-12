# Environment Variables Reference

Every variable the backend and frontend read, in one place. The backend reads its variables
through `app/config/settings.py` (a single `pydantic-settings` `Settings` object — see
`docs/architecture.md`), case-insensitively, so `OPENAI_API_KEY` and `openai_api_key` are the
same variable; this doc uses the `UPPER_SNAKE_CASE` env var form throughout since that's what
actually goes in `.env` / a container's environment / an ECS task definition.

`.env.example` at the repo root is the copy-pasteable source of truth for local development;
this document is the explanatory reference — what each variable does, whether it's a secret,
and how it's supplied in each of the three ways this project runs: bare `uvicorn`/`npm run dev`,
`docker compose`, and AWS (see `docs/aws-deployment.md`).

## How to read the tables

- **Secret** — must never be committed, logged, or baked into a public artifact. In AWS these
  are resolved from Secrets Manager/SSM at task-start, not passed as plain task-definition
  environment variables (see `docs/aws-deployment.md`).
- **Build-time** (frontend only) — a `NEXT_PUBLIC_*` variable Next.js inlines into the client
  JavaScript bundle when `npm run build` runs. There is no way to change one of these for an
  already-built image/artifact short of rebuilding it; setting it as a container *runtime*
  environment variable does nothing.
- **Runtime** — read when the process starts (or, for `pydantic-settings`, effectively once,
  since `get_settings()` is `@lru_cache`d — restart the process to pick up a change).

## Backend

### Application

| Variable | Secret? | Default | Required | Description |
|---|---|---|---|---|
| `APP_ENV` | no | `development` | no | `development`, `test`, or `production`. Informational/for future environment-specific branching — nothing currently branches on it beyond documenting intent. |
| `LOG_LEVEL` | no | `INFO` | no | Passed to `logging.getLogger().setLevel()`. Any standard Python level name. |
| `CORS_ORIGINS` | no | `["http://localhost:3000"]` | no | JSON array of allowed browser origins for `CORSMiddleware`. Must include the frontend's real origin in every environment — see the note in `docs/aws-deployment.md` about this being the single most common first-deploy misconfiguration. |

### Authentication

| Variable | Secret? | Default | Required | Description |
|---|---|---|---|---|
| `API_KEYS` | **yes** | `[]` (empty) | **yes, effectively** | JSON array of accepted `X-API-Key` values. Fail-closed: empty means every `/api/v1/*` request is rejected, not that auth is disabled — see `docs/security-architecture.md` section 9. No default is shipped on purpose (a default credential is itself a vulnerability). Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. |

### LLM provider

| Variable | Secret? | Default | Required | Description |
|---|---|---|---|---|
| `LLM_PROVIDER` | no | `openai` | no | `openai` or `anthropic` — which chat model backs every agent node. Switching this is a config change, not a code change (`app/llm/provider.py`). |
| `OPENAI_API_KEY` | **yes** | — | **yes** | Required regardless of `LLM_PROVIDER` — embeddings are always OpenAI (`docs/design-decisions.md` #2), so this is needed even when `LLM_PROVIDER=anthropic`. |
| `ANTHROPIC_API_KEY` | **yes** | — | only if `LLM_PROVIDER=anthropic` | |
| `OPENAI_CHAT_MODEL` | no | `gpt-4o` | no | |
| `ANTHROPIC_CHAT_MODEL` | no | `claude-sonnet-5` | no | |
| `LLM_TEMPERATURE` | no | `0.0` | no | Deterministic by default — appropriate for a claims-decision system that has to justify itself, not a creative-writing one. |
| `OPENAI_EMBEDDING_MODEL` | no | `text-embedding-3-small` | no | |

### Storage

| Variable | Secret? | Default | Required | Description |
|---|---|---|---|---|
| `DATABASE_URL` | no (but see below) | `sqlite:///./data/claims.db` | no | SQLAlchemy URL. **A local file path in a container context implies a volume** — without one, the database is lost on every container restart/redeploy. `docker-compose.yml` mounts `backend_data:/app/data`; the ECS deployment mounts an EFS access point at the same path (`docs/aws-deployment.md`). |
| `VECTOR_INDEX_DIR` | no | `./data/indices` | no | Where the FAISS `.faiss` index files live. Same volume-persistence requirement as `DATABASE_URL`. |
| `POLICY_CORPUS_DIR` | no | `./data/policy_corpus` | no | Source documents for `scripts/build_policy_index.py`. Shipped inside the image (`docker/backend.Dockerfile` copies `backend/data/`), so this one specifically does *not* need to be on the persistent volume — it's rebuilt from image content, not runtime state. |
| `SYNTHETIC_CLAIMS_DIR` | no | `./data/synthetic_claims` | no | Output of `scripts/generate_synthetic_claims.py`. Needs the persistent volume (it's generated at runtime, not shipped in the image). |
| `UPLOAD_STORAGE_DIR` | no | `./data/uploads` | no | Where uploaded claim PDFs are written. Needs the persistent volume. |

### RAG

| Variable | Secret? | Default | Required | Description |
|---|---|---|---|---|
| `RAG_SIMILARITY_THRESHOLD` | no | `0.65` | no | Dense-score cutoff below which a retrieved chunk is flagged `low_confidence` — see `docs/vector-db-architecture.md`. |
| `RAG_TOP_K` | no | `5` | no | Chunks retrieved per source per query. |

### Self-Critic retry loop

| Variable | Secret? | Default | Required | Description |
|---|---|---|---|---|
| `SELF_CRITIC_SCORE_THRESHOLD` | no | `0.80` | no | Spec-fixed value; see `docs/design-decisions.md` "Open items" for the calibration caveat. |
| `SELF_CRITIC_MAX_RETRIES` | no | `2` | no | Hard cap enforced by `app/agents/routing.py`, independent of this value ever being misconfigured to something huge — see `docs/langgraph-workflow.md`. |

### Security

| Variable | Secret? | Default | Required | Description |
|---|---|---|---|---|
| `SECURITY_BLOCK_CONFIDENCE` | no | `0.70` | no | LLM classifier confidence above which Security Checker's LLM layer alone blocks a claim (the heuristic layer blocks independently of this value — see `docs/security-architecture.md` section 3). |
| `UPLOAD_MAX_BYTES` | no | `15000000` (15 MB) | no | Per-file upload size limit. |
| `ALLOWED_UPLOAD_CONTENT_TYPES` | no | `["application/pdf"]` | no | JSON array of accepted MIME types. |

## Frontend

All three are `NEXT_PUBLIC_*` **build-time** variables (see "How to read the tables" above) —
never read at container runtime, only at `npm run build` / `docker build` time.

| Variable | Secret? | Default | Required | Description |
|---|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | no | `http://localhost:8000` | **yes** | Base URL the browser calls for every REST request (`frontend/lib/api.ts`). Must be the backend's real, publicly-reachable URL in any non-local environment. |
| `NEXT_PUBLIC_WS_BASE_URL` | no | `ws://localhost:8000` | **yes** | Base URL for the Processing screen's WebSocket connection (`frontend/lib/websocket.ts`). `wss://` (not `ws://`) once the backend is behind TLS — see the mixed-content note in `docs/aws-deployment.md`. |
| `NEXT_PUBLIC_API_KEY` | **yes, but browser-visible — see below** | — | **yes** | Must match one of the values in the backend's `API_KEYS`. `docker-compose.yml`'s frontend build fails fast with a clear error if this is unset (`${NEXT_PUBLIC_API_KEY:?...}`) rather than silently baking in an empty key. |

**Why `NEXT_PUBLIC_API_KEY` is listed as a secret despite being visible in the browser:** it must
still be *generated* and *distributed* like a secret (not committed, not guessable) even though,
once built, it's readable by anyone who opens browser dev tools — this is the explicit, documented
scope tradeoff in `docs/security-architecture.md` section 9 ("Honest scope note on the
browser-embedded key"): the auth scheme here is a shared secret between this project's own
frontend and backend, not a defense against a hostile public client.

## Where each variable is actually supplied

| Context | Backend variables | Frontend variables |
|---|---|---|
| Bare `uvicorn` / `npm run dev` | `backend/.env` (loaded by `pydantic-settings`, see `env_file=".env"` in `Settings`) | `frontend/.env.local` |
| `docker compose up` | Repo-root `.env`, loaded via `env_file:` on the `backend` service | Repo-root `.env`, read directly by Compose for `${VAR}` substitution into the frontend's build `args:` — a *different* mechanism from the backend's `env_file:`, which is why both point at the same file but are configured separately in `docker-compose.yml` |
| AWS (ECS Fargate) | Non-secret values as plain `environment` entries in the task definition; `API_KEYS`/`OPENAI_API_KEY`/`ANTHROPIC_API_KEY` as `secrets` entries resolved from AWS Secrets Manager at task start — see `docs/aws-deployment.md` | Baked into the frontend Docker image at build time in the CD pipeline (`.github/workflows/deploy.yml`), sourced from GitHub Actions repository secrets/variables — there is no ECS-task-level equivalent for these, since they're compiled in before the image ever reaches ECS |

## Adding a new variable

1. Add the field to `Settings` in `backend/app/config/settings.py` (backend) or read it via
   `process.env.NEXT_PUBLIC_*` (frontend — remember the `NEXT_PUBLIC_` prefix is what makes
   Next.js expose it to the browser at all; anything without that prefix is server-only and
   silently `undefined` in client components).
2. Add it to `.env.example` with a comment.
3. Add a row to this document.
4. If it's required in production, add it to the ECS task definition in
   `infra/aws/ecs-stack.yaml` (as a `secrets` entry if sensitive, `environment` otherwise) and
   to the frontend build-args list in `.github/workflows/deploy.yml` if it's a `NEXT_PUBLIC_*`
   value.
