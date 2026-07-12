# US Insurance Claim Processing Agent

A multi-agent LangGraph pipeline that processes US insurance claims: it parses uploaded claim
documents, validates them against public-domain US policy rules, detects fraud signals, and
produces a structured claim decision — 9 agents wired as a LangGraph `StateGraph` with
conditional routing, a hybrid prompt-injection security gate, hybrid (dense+sparse) 3-source RAG
with an embedding cache and incremental indexing, and a self-critique retry loop.

## Status

This repository currently contains the **complete project skeleton**: every module, agent node,
API route, database model, and frontend screen is wired end-to-end with real (not stubbed)
control flow, and the full backend test suite (136 tests: unit, integration, LangGraph
full-pipeline, and security) passes, alongside a frontend test suite (30 tests, Vitest +
Testing Library). The RAG layer is production-shaped: hybrid dense+sparse retrieval with
Reciprocal Rank Fusion, a populated 6-document policy corpus, a persistent embedding cache,
genuinely incremental ingestion (verified: a re-run over an unchanged corpus makes zero new
embedding calls), and an evaluation harness (`scripts/evaluate_retrieval.py`) comparing hybrid
against dense-only recall. See [docs/vector-db-architecture.md](docs/vector-db-architecture.md).

All 5 required test claim scenarios are done: `test_scenarios/` has real, generated PDF fixtures
for full approval, partial approval, denial, fraud detection, and the spec's named prompt-injection
attack, each with an automated proof (`backend/tests/langgraph/` and `backend/tests/security/`)
that runs the fixture through the actual production graph end-to-end, not a node in isolation or
a raw-string unit test. See [test_scenarios/README.md](test_scenarios/README.md).

The API surface is production-shaped: every `/api/v1/*` route requires an `X-API-Key`
(fail-closed — an unset `API_KEYS` rejects everyone, never lets everyone through), a raw ASGI
middleware assigns a request-correlation id that's automatically stamped onto every log line
emitted anywhere during that request, unhandled exceptions are caught and logged without ever
leaking a stack trace to the client, `/health` and `/health/ready` give an orchestrator real
liveness/readiness signals (DB + both vector indices), and the dispute chat has a token-streaming
SSE variant alongside the blocking JSON one. See
[docs/api-architecture.md](docs/api-architecture.md) and
[docs/security-architecture.md](docs/security-architecture.md) section 9.

What's intentionally *not* yet filled in:

- Agent prompts are real and specific but not yet tuned/calibrated against the 5 test scenarios
  against a live model — the automated tests script the LLM layer deterministically (see
  "How the test suite is organized" below) rather than depending on live API calls.

See [docs/README.md](docs/README.md) for the full architecture record this was built against.

## How the test suite is organized

| Layer | Where | What it covers |
|---|---|---|
| Unit | `backend/tests/unit/` | Pure logic and per-node behavior with fakes: chunking, hybrid retrieval/fusion, embedding cache, PII redaction, injection heuristics, routing predicates, one file per agent node |
| LangGraph (full pipeline) | `backend/tests/langgraph/` | `build_claim_graph` end-to-end against real PDF fixtures for all 5 required scenarios, plus the Self-Critic retry loop exercised through the real conditional edge |
| API / integration | `backend/tests/integration/` | Auth, middleware, exception handling, health/readiness, and every REST route's HTTP contract against a real (temp SQLite) database |
| Security | `backend/tests/security/` | The two malicious-PDF injection cases (heuristic-only and LLM-only blocking) plus PII flagging, run through the real production graph |
| Frontend | `frontend/**/*.test.{ts,tsx}` | SSE parsing, pure display logic (`computeProgress`, status/label mappings), and component behavior (file filtering, typing-indicator state) via Vitest + Testing Library |

Every backend test — including the full-pipeline ones — runs with a scripted fake chat model
(`backend/tests/fakes.py`), never a live LLM call: deterministic, free, and safe in CI with no
API key. See `test_scenarios/README.md` for what that does and doesn't prove.

## Architecture

| Doc | Covers |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Folder structure, component diagram, tech stack |
| [docs/agent-architecture.md](docs/agent-architecture.md) | The 9 agents and state ownership |
| [docs/langgraph-workflow.md](docs/langgraph-workflow.md) | StateGraph wiring, conditional routing, retry loop |
| [docs/api-architecture.md](docs/api-architecture.md) | REST + WebSocket surface, layering |
| [docs/database-architecture.md](docs/database-architecture.md) | Relational schema (SQLite) |
| [docs/vector-db-architecture.md](docs/vector-db-architecture.md) | FAISS index design |
| [docs/memory-architecture.md](docs/memory-architecture.md) | Short/long-term memory, dispute flow |
| [docs/security-architecture.md](docs/security-architecture.md) | Hybrid injection detection, PII redaction |
| [docs/design-decisions.md](docs/design-decisions.md) | Decision log — what was chosen, rejected, why |

## Project layout

```
.
├── backend/          FastAPI + LangGraph backend (Python 3.11)
├── frontend/          Next.js + TypeScript + Tailwind frontend
├── docker/            Dockerfiles for both services
├── docs/              Architecture documentation (read this first)
├── test_scenarios/    5 required claim scenarios (see below)
└── docker-compose.yml
```

## Quickstart

### Prerequisites

- Python 3.11+
- Node.js 20+
- An OpenAI API key (required for embeddings regardless of `LLM_PROVIDER` — see
  [docs/design-decisions.md](docs/design-decisions.md) decision #2) and/or an Anthropic API key

### 1. Configure environment

```bash
cp .env.example backend/.env      # fill in OPENAI_API_KEY (and ANTHROPIC_API_KEY if used)
cp frontend/.env.example frontend/.env.local
```

Generate a real API key and set it in **both** files — auth is fail-closed, so the backend
rejects every `/api/v1/*` request until this is set:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# → put the result in backend/.env's API_KEYS=["..."] and
#   frontend/.env.local's NEXT_PUBLIC_API_KEY=...
```

### 2. Backend

```bash
make backend-install
make init-db
make build-index      # builds/updates the policy_corpus hybrid index (incremental — safe to re-run)
make seed-claims       # generates + indexes synthetic historical claim decisions
make backend-dev        # http://localhost:8000 — interactive docs at /docs
```

To evaluate retrieval quality (hybrid vs. dense-only recall@k against the policy corpus):

```bash
cd backend && python -m scripts.evaluate_retrieval
```

### 3. Frontend

```bash
make frontend-install
make frontend-dev       # http://localhost:3000
```

### 4. Run the tests

```bash
make backend-test       # 136 tests: unit, LangGraph full-pipeline, integration, security
make frontend-test      # 30 tests: Vitest + Testing Library
make frontend-typecheck
make frontend-build
```

### Docker

```bash
cp .env.example .env    # docker-compose reads this via env_file
make docker-up          # backend on :8000, frontend on :3000
```

The `backend_data` named volume persists the SQLite DB, FAISS indices, and uploads across
container restarts. After the first `docker compose up`, run the corpus/seed scripts inside the
container once:

```bash
docker compose exec backend python -m scripts.build_policy_index
docker compose exec backend python -m scripts.generate_synthetic_claims
```

## The 9-agent pipeline

```
Document Preprocessor → Intent Analyzer → RAG Retriever → Security Checker
    → [BLOCKED if injection detected]
    → Coverage Validator → Fraud Detector → Answer Synthesizer → Self-Critic
        → [retry Answer Synthesizer with critique, max 2 retries]
    → Final Output
```

Full diagram and per-agent responsibilities: [docs/agent-architecture.md](docs/agent-architecture.md).

## Frontend screens

| Route | Screen |
|---|---|
| `/submit` | Claim Submission — upload documents, enter query |
| `/processing/[claimId]` | Processing View — live per-agent status over WebSocket |
| `/decision/[claimId]` | Decision Dashboard — badge, coverage table, fraud panel, citations, attorney flag |
| `/dispute/[claimId]` | Dispute Flow — multi-turn chat contesting a decision |
| `/audit/[claimId]` | Audit Trail — full timestamped agent execution log |

## Acceptance criteria checklist

Non-negotiable criteria from the spec, and where each is implemented:

- [x] All 9 LangGraph nodes correctly wired with conditional routing — `backend/app/agents/graph.py`
- [x] Shared state flows without data loss across all agents — `backend/app/state/graph_state.py` (namespaced fields, `operator.add` audit_log reducer)
- [x] Security Checker catches embedded prompt injection — hybrid heuristic + LLM classifier, `backend/app/security/injection_detector.py`; end-to-end proof against real malicious PDFs, run through the actual production graph, in `backend/tests/security/test_malicious_pdf_injection.py`
- [x] RAG retrieves from all three sources with source metadata attached — `backend/app/agents/nodes/rag_retriever.py`, hybrid dense+sparse retrieval via `backend/app/vectorstore/hybrid_store.py`
- [x] Self-Critic injects critique into Synthesizer on retry — `backend/app/prompts/answer_synthesizer_prompt.py` (critique is a required prompt-template field, not optional context)
- [x] `retry_count` guard prevents infinite loops — `backend/app/agents/routing.py` (`route_after_critic` + dedicated `prepare_retry` node)
- [x] Every claim decision cites a specific clause or statute — enforced at the structured-output schema level in `backend/app/agents/nodes/coverage_validator.py`
- [x] `audit_log` contains a timestamped entry from every agent — `backend/app/core/audit.py`, called by every node
- [x] `attorney_flag` triggers on high-severity fraud or high-risk legal interpretation — `backend/app/agents/nodes/fraud_detector.py`

## Deliverables checklist

- [x] GitHub repo with README and setup instructions
- [x] LangGraph agent code — each node in its own file with its own system prompt
- [x] RAG ingestion script + vector store setup using public corpus — `backend/scripts/build_policy_index.py` (incremental, multi-format), 6-document representative corpus in `backend/data/policy_corpus/`
- [x] FastAPI backend + WebSocket streaming endpoint — plus API-key auth, request-id/access-log middleware, structured JSON logging, `RequestValidationError`/catch-all exception handlers, liveness+readiness health checks, and an SSE token-streaming variant of the dispute endpoint; see [docs/api-architecture.md](docs/api-architecture.md)
- [x] React frontend with all 5 screens
- [x] 5 test claim scenarios (fraud, partial approval, denial, etc.) — real generated PDF fixtures for all 5 in `test_scenarios/`, each with an automated proof in `backend/tests/langgraph/` running the fixture through the production graph end-to-end
- [x] Security test: documented proof PDF injection is caught — real generated PDF fixtures in `test_scenarios/05_prompt_injection_attack/`, run end-to-end through the production graph in `backend/tests/security/test_malicious_pdf_injection.py`
- [x] `.env.example` with all required configuration keys

## License

MIT
