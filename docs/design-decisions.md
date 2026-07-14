# Design Decisions

A running log of choices made, alternatives considered, and why.

## 1. Domain: medication interaction & prescription safety checker

Chosen over alternatives (clinical triage assistant, medical-records Q&A, prior-authorization
agent) because it has a clean multi-agent decomposition (parse → normalize → retrieve →
check → check → check → synthesize → critique → finalize), a natural RAG use case (drug
interaction monographs), and a well-defined non-diagnostic scope: this system flags risks for
a pharmacist/prescriber to review, it never approves or denies a prescription itself.

## 2. Deterministic checks for interaction/allergy/dosage, LLM only for parsing and synthesis

See `docs/agent-architecture.md`'s "why deterministic checks do most of the work" section.
The short version: interaction/allergy/dosage logic against a reference table has a
verifiably correct answer; an LLM would only add non-determinism and untestable failure
modes. The LLM's value-add is turning free text into structure (Parser) and turning three
structured finding lists into one coherent, prioritized narrative (Synthesizer/Critic).

## 3. A curated 10-monograph corpus, not a scrape of a real drug database

Real interaction databases (Micromedex, Lexicomp, First Databank) are commercially licensed
and not redistributable in an open project. The 10 monographs here are original, clinically
accurate summaries covering well-known interactions, sized to make the project's test
scenarios concrete and verifiable — not a claim of exhaustive pharmacological coverage. A
production system would license a real interaction database and swap it in behind the same
`InteractionRetriever` interface.

## 4. FAISS + embedding cache instead of a managed vector DB

See `docs/rag-architecture.md`. Ten documents don't justify Pinecone/Weaviate-style
infrastructure; local FAISS plus a persisted embedding cache gets genuine incremental
indexing (proven in `test_embedding_cache.py`) without any extra service to run.

## 5. Approximate dose-range validation, not a full pharmacokinetic model

`dosage_validator.py` compares a parsed `dose_value`/`dose_unit` against a fixed adult daily
range and a renal-function-keyed adjustment note. It does not compute weight-based dosing,
account for drug half-life/accumulation, or model hepatic clearance beyond a
hepatic_function field that isn't yet consulted by the validator (only renal_function is).
This is flagged rather than hidden: a real clinical dosing engine is a project of its own,
and pretending otherwise here would be worse than being explicit about the simplification.

## 6. Single in-process progress broadcaster, not a message broker

`backend/app/services/broadcaster.py` is a plain in-memory pub/sub. It works because this
project's deployment model is a single backend process talking to a single SQLite file (see
`docs/database-architecture.md`'s single-writer note). Scaling to multiple backend replicas
would need a shared broker (Redis pub/sub, etc.) — noted here so it isn't a surprise later.

## 7. React + Vite instead of Next.js

The frontend doesn't need server-side rendering or file-based API routes — it's a client
rendered against a separate FastAPI backend. Vite gives a much simpler, faster dev/build
loop for that shape of app than Next.js would.
