# Architecture Documentation

This directory is the architecture record for the **US Insurance Claim Processing Agent** — produced before any implementation code, per the interview spec's requirement to design before building.

Read in this order:

| Doc | Covers |
|---|---|
| [architecture.md](./architecture.md) | Folder structure, component diagram, tech stack, system overview |
| [agent-architecture.md](./agent-architecture.md) | The 9 agents, their responsibilities, and state-field ownership |
| [langgraph-workflow.md](./langgraph-workflow.md) | StateGraph node/edge wiring, conditional routing, retry loop mechanics |
| [api-architecture.md](./api-architecture.md) | REST + WebSocket surface, layering, sequence diagrams |
| [database-architecture.md](./database-architecture.md) | Relational schema (SQLite) for claims, decisions, disputes, audit log |
| [vector-db-architecture.md](./vector-db-architecture.md) | FAISS index design for the three RAG sources |
| [memory-architecture.md](./memory-architecture.md) | Short-term checkpointing, long-term store, dispute conversation memory |
| [security-architecture.md](./security-architecture.md) | Hybrid injection detection, PII redaction, hard-block enforcement, defense-in-depth |
| [design-decisions.md](./design-decisions.md) | Consolidated decision log — what was chosen, what was rejected, why |

No implementation code exists yet. This is the design gate: once approved, Milestone 0 (scaffolding) begins against this document.
