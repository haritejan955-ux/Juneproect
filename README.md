# Medication Interaction & Prescription Safety Checker

A multi-agent LangGraph pipeline for medication safety review: it parses a patient's
prescription list, normalizes drug names against a local reference table, retrieves known
drug-drug interactions from a monograph knowledge base via hybrid RAG + metadata
verification, cross-checks allergies/contraindications and dose ranges, and synthesizes a
severity-ranked safety report with a self-critique retry loop — 9 agents wired as a
LangGraph `StateGraph` with conditional routing, a hybrid prompt-injection security gate on
all free-text input, and a pharmacist-review flag on high-severity findings.

This is a clinical **decision-support** tool: it flags risks for a pharmacist or prescriber
to review. It never approves, denies, or auto-adjusts a prescription itself.

## Status

Complete project skeleton: every module, agent node, API route, database model, and frontend
screen is wired end-to-end with real (not stubbed) control flow. The full backend test suite
(53 tests: unit, LangGraph full-pipeline, integration, security) passes, alongside a frontend
test suite (8 tests, Vitest + Testing Library). `ruff`, `mypy`, `tsc`, and `eslint` are all
clean.

The RAG layer: hybrid FAISS retrieval with a persisted embedding cache — genuinely
incremental (re-running the index build over an unchanged corpus makes zero new embedding
calls, proven in `backend/tests/unit/test_embedding_cache.py`) — and metadata-verified
citations (see [docs/rag-architecture.md](docs/rag-architecture.md)).

All 5 required scenarios have automated proofs running the fixture through the actual
production graph end-to-end (`backend/tests/langgraph/`): a safe prescription with no
findings, a major drug-drug interaction (warfarin + aspirin), an allergy contraindication
(penicillin allergy + amoxicillin), a dosage/renal-impairment issue (metformin), and the
Self-Critic retry loop exercised through its real conditional edge. The prompt-injection
security gate has its own end-to-end proof in `backend/tests/security/`.

What's intentionally *not* filled in — see
[docs/design-decisions.md](docs/design-decisions.md) for the reasoning behind each:

- Agent prompts are real and specific but not yet tuned against a live model — every
  automated test scripts the LLM layer deterministically (see below) rather than depending on
  live API calls.
- The interaction corpus is a curated set of 10 representative monographs, not a licensed
  real-world drug database (those are proprietary and not redistributable).
- Dosage validation is an approximate adult-range + renal-adjustment check, not a full
  pharmacokinetic model.

## How the test suite is organized

| Layer | Where | What it covers |
|---|---|---|
| Unit | `backend/tests/unit/` | Pure logic and per-node behavior with fakes: drug normalization, allergy/dosage checks, interaction retrieval, embedding cache, injection heuristics, routing predicates — one file per agent node |
| LangGraph (full pipeline) | `backend/tests/langgraph/` | `build_safety_graph` end-to-end against all 5 required scenarios, plus the Self-Critic retry loop exercised through the real conditional edge |
| API / integration | `backend/tests/integration/` | Auth, health/readiness, and every REST route's HTTP contract against a real (temp SQLite) database |
| Security | `backend/tests/security/` | Heuristic-caught and LLM-classifier-caught injection attempts, plus a legitimate-clinical-text control case, run through the real production graph |
| Frontend | `frontend/src/**/*.test.{ts,tsx}` | API client behavior, WebSocket progress-tracking logic, and component rendering (SubmitPage form flow, FindingsList, SeverityBadge) |

Every backend test — including the full-pipeline ones — runs with a scripted fake chat model
and a deterministic bag-of-words fake embedding (`backend/tests/fakes.py`), never a live LLM
or embeddings call: free, fast, and safe in CI with no API key.

## Architecture

| Doc | Covers |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Folder structure, component diagram, tech stack |
| [docs/agent-architecture.md](docs/agent-architecture.md) | The 9 agents and state ownership |
| [docs/langgraph-workflow.md](docs/langgraph-workflow.md) | StateGraph wiring, conditional routing, retry loop |
| [docs/api-architecture.md](docs/api-architecture.md) | REST + WebSocket surface, auth, background processing |
| [docs/database-architecture.md](docs/database-architecture.md) | Relational schema (SQLite) |
| [docs/rag-architecture.md](docs/rag-architecture.md) | FAISS index design, embedding cache, citation verification |
| [docs/security-architecture.md](docs/security-architecture.md) | Hybrid injection detection |
| [docs/design-decisions.md](docs/design-decisions.md) | Decision log — what was chosen, rejected, why |
| [docs/deployment.md](docs/deployment.md) | Docker Compose, secrets, single-writer SQLite constraint, CI |
| [docs/environment-variables.md](docs/environment-variables.md) | Every backend and frontend variable |

## Project layout

```
.
├── backend/          FastAPI + LangGraph backend (Python 3.11)
├── frontend/          React + Vite + TypeScript + Tailwind frontend
├── docker/            Dockerfiles for both services
├── docs/              Architecture documentation (read this first)
└── docker-compose.yml
```

## Quickstart

### Prerequisites

- Python 3.11+
- Node.js 20+
- An OpenAI API key (required for embeddings regardless of `LLM_PROVIDER`) and/or an
  Anthropic API key

### 1. Configure environment

```bash
cp backend/.env.example backend/.env    # fill in OPENAI_API_KEY (and ANTHROPIC_API_KEY if used)
cp frontend/.env.example frontend/.env.local
```

Generate a real API key and set it in **both** files — auth is fail-closed, so the backend
rejects every `/api/v1/*` request until this is set:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# → put the result in backend/.env's API_KEYS=["..."] and
#   frontend/.env.local's VITE_API_KEY=...
```

### 2. Backend

```bash
make backend-install
make init-db
make build-index      # builds the interaction-corpus FAISS index (incremental — safe to re-run)
make backend-dev      # http://localhost:8000 — interactive docs at /docs
```

### 3. Frontend

```bash
make frontend-install
make frontend-dev     # http://localhost:5173
```

### 4. Run the tests and static analysis

```bash
make backend-test        # 53 tests: unit, LangGraph full-pipeline, integration, security
make backend-lint         # ruff
make backend-typecheck    # mypy
make frontend-test        # 8 tests: Vitest + Testing Library
make frontend-typecheck   # tsc --noEmit
make frontend-lint        # eslint
make frontend-build
```

### Docker

```bash
cp .env.example .env    # docker-compose reads this via env_file
make docker-up          # backend on :8000, frontend on :3000
docker compose exec backend python -m scripts.build_interaction_index
```

## Deployment

See [docs/deployment.md](docs/deployment.md) for the full picture: Docker Compose setup,
secrets handling, the single-writer SQLite constraint and what changes to scale past it, TLS
termination, and the CI pipeline (`.github/workflows/ci.yml`).

## The 9-agent pipeline

```
Prescription Parser → Drug Normalizer → Patient Profile Loader → Interaction Retriever (RAG)
    → [BLOCKED if prompt injection detected]
    → Allergy & Contraindication Checker → Dosage Validator → Risk Synthesizer → Self-Critic
        → [retry Risk Synthesizer with critique, max 2 retries]
    → Final Output (pharmacist_review_flag)
```

Full diagram and per-agent responsibilities: [docs/agent-architecture.md](docs/agent-architecture.md).

## Frontend screens

| Route | Screen |
|---|---|
| `/submit` | Prescription + patient profile submission form |
| `/processing/:reportId` | Live per-agent progress over WebSocket |
| `/report/:reportId` | Safety report — severity badge, medications table, findings, pharmacist-review banner, audit trail |
| `/history` | Recent reports list |

## Acceptance criteria checklist

- [x] All 9 LangGraph nodes correctly wired with conditional routing — `backend/app/agents/graph.py`
- [x] Shared state flows without data loss across all agents — `backend/app/state/graph_state.py` (`operator.add` audit_log reducer)
- [x] Security Checker catches embedded prompt injection — hybrid heuristic + LLM classifier, `backend/app/security/injection_detector.py`; end-to-end proof in `backend/tests/security/test_prompt_injection.py`
- [x] RAG retrieves from the interaction knowledge base with source metadata attached — `backend/app/agents/nodes/interaction_retriever.py`, `backend/app/rag/store.py`
- [x] Self-Critic injects critique into the Synthesizer on retry — `backend/app/prompts/risk_synthesizer_prompt.py`
- [x] `retry_count` guard prevents infinite loops — `backend/app/agents/routing.py` (`route_after_critic` + dedicated `prepare_retry` node)
- [x] Every interaction finding cites a specific monograph — enforced by the retriever's metadata-verified citation attachment
- [x] `audit_log` contains a timestamped entry from every agent — `backend/app/core/audit.py`, called by every node
- [x] `pharmacist_review_flag` triggers on major/contraindicated severity findings — `backend/app/agents/nodes/final_output.py`

## Deliverables checklist

- [x] GitHub repo with README and setup instructions
- [x] LangGraph agent code — each node in its own file, LLM-backed nodes each with their own system prompt
- [x] RAG ingestion script + vector store setup over a curated corpus — `backend/scripts/build_interaction_index.py`, 10-document monograph corpus in `backend/app/data/interaction_corpus/`
- [x] FastAPI backend + WebSocket streaming endpoint — plus API-key auth, request-id/access-log middleware, structured JSON logging, exception handlers, liveness+readiness health checks
- [x] React frontend with all 4 screens
- [x] 5 test scenarios (major interaction, allergy conflict, dosage/renal issue, safe case, self-critic retry) — each with an automated proof running the fixture through the production graph end-to-end
- [x] Security test: documented proof of prompt-injection detection — `backend/tests/security/test_prompt_injection.py`
- [x] `.env.example` files with all required configuration keys

## License

MIT
