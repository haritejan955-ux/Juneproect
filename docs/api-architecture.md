# API Architecture

FastAPI app factory in `backend/app/main.py`.

## Auth

Every `/api/v1/*` route requires an `X-API-Key` header, checked in
`backend/app/core/auth.py::require_api_key`, applied as a router-level dependency. It is
**fail-closed**: if `API_KEYS` is unset or empty, every request is rejected — an empty
config never accidentally means "everyone's allowed in." `/health` and `/health/ready` are
intentionally unauthenticated (an orchestrator's liveness probe shouldn't need a secret).

The WebSocket endpoint can't use a request header (browser `WebSocket` API doesn't support
custom headers), so it takes `?api_key=` as a query parameter, checked against the same
`API_KEYS` list before `accept()`.

## Middleware

`RequestContextMiddleware` (`backend/app/core/middleware.py`) assigns a UUID request id per
request, stores it in a `contextvars.ContextVar`, and a logging filter stamps it onto every
log line emitted anywhere during that request — including inside a node deep in a LangGraph
run, since Python's `contextvars` propagate across the async call graph. It also echoes the
id back as an `X-Request-ID` response header and logs one structured access-log line per
request (method, path, status, duration).

## Exception handling

Three handlers in `main.py`: `RequestValidationError` → 422 with the Pydantic error detail;
`HTTPException` → whatever status/detail the route raised; and a catch-all `Exception`
handler that logs the full traceback server-side but returns a generic 500 with no stack
trace to the client.

## Routes

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/reports` | Submit a prescription + patient profile. Creates `Patient` + `SafetyReport` rows (status `processing`), kicks off the graph run as a background task, returns `202` with the `report_id` immediately. |
| `GET` | `/api/v1/reports/{id}` | Fetch the current state of a report (whatever status it's in). |
| `GET` | `/api/v1/reports/{id}/audit` | Full timestamped per-agent audit trail. |
| `GET` | `/api/v1/reports` | Recent reports, paginated (`limit`, default 20, max 100). |
| `WS` | `/ws/reports/{id}?api_key=...` | Live per-agent progress. If the report already finished by the time a client connects, sends one `complete` event and closes; otherwise streams `progress` events as each node finishes, then one `complete` event. |
| `GET` | `/health` | Liveness — always `200 {"status": "ok"}` if the process is up. |
| `GET` | `/health/ready` | Readiness — checks DB connectivity and that the interaction FAISS index is loadable; `503` if either check fails. |

## Background processing model

`POST /reports` doesn't block on the LLM-bound graph run. It creates the DB rows and returns
immediately; `asyncio.create_task(process_report(...))` runs the graph on a worker thread,
publishes progress to an in-process broadcaster (`backend/app/services/broadcaster.py`) that
the WebSocket endpoint subscribes to, and persists the final state (medications, findings,
summary, `pharmacist_review_flag`, full audit trail) back onto the `SafetyReport` row when
done. This is single-process pub/sub — it matches the single-writer SQLite deployment model
(see `docs/deployment.md`) and would need a real message broker (Redis, etc.) to scale past
one backend instance.
