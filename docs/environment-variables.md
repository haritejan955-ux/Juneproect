# Environment Variables

## Backend (`backend/.env`, see `backend/.env.example`)

| Variable | Secret? | Purpose |
|---|---|---|
| `API_KEYS` | Yes | JSON list of accepted `X-API-Key` values. Fail-closed if unset/empty. |
| `LLM_PROVIDER` | No | `openai` or `anthropic`. Selects the chat model used by the Parser, Synthesizer, and Critic nodes. |
| `OPENAI_API_KEY` | Yes | Required regardless of `LLM_PROVIDER` — embeddings (for the interaction-corpus index) always use OpenAI. |
| `ANTHROPIC_API_KEY` | Yes | Required only if `LLM_PROVIDER=anthropic`. |
| `OPENAI_MODEL` | No | Chat model name when `LLM_PROVIDER=openai`. Default `gpt-4o-mini`. |
| `ANTHROPIC_MODEL` | No | Chat model name when `LLM_PROVIDER=anthropic`. Default `claude-sonnet-5`. |
| `EMBEDDING_MODEL` | No | OpenAI embedding model for the interaction index. Default `text-embedding-3-small`. |
| `MAX_SYNTHESIS_RETRIES` | No | Self-Critic retry cap. Default `2`. |
| `DATABASE_URL` | No | SQLAlchemy async URL. Default `sqlite+aiosqlite:///./data/app.db`. |
| `ENVIRONMENT` | No | Free-text environment label (`development`/`production`), informational. |
| `LOG_LEVEL` | No | Python logging level. Default `INFO`. |
| `CORS_ORIGINS` | No | JSON list of allowed frontend origins. |

## Frontend (`frontend/.env.local`, see `frontend/.env.example`)

| Variable | Secret? | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | No | Backend base URL, e.g. `http://localhost:8000`. Compile-time (Vite). |
| `VITE_API_KEY` | Yes* | Sent as `X-API-Key` on every API call and `?api_key=` on the WebSocket. |

\* This is a demo-project simplification: the API key ends up in the shipped frontend
bundle, which is fine for a single-tenant/internal tool but is **not** an appropriate auth
model for a public-facing production deployment — that would need per-user auth (e.g. OAuth)
issued to the browser at runtime, not a static key baked into the build.
