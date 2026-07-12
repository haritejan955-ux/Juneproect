# Architecture Documentation

This directory is the architecture record for the **US Insurance Claim Processing Agent**. It
was written before implementation began, per the interview spec's requirement to design before
building, and is kept up to date as the design's canonical reference now that the project
skeleton (`backend/`, `frontend/`) exists and matches it.

Read in this order:

| Doc | Covers |
|---|---|
| [architecture.md](./architecture.md) | Folder structure, component diagram, tech stack, system overview |
| [agent-architecture.md](./agent-architecture.md) | The 9 agents, their responsibilities, and state-field ownership |
| [langgraph-design.md](./langgraph-design.md) | The complete LangGraph design: state, every node, edges, conditional routing, retry loop, MemorySaver, checkpointing, audit log, shared state — with diagrams |
| [langgraph-workflow.md](./langgraph-workflow.md) | StateGraph node/edge wiring, conditional routing, retry loop mechanics (companion to langgraph-design.md) |
| [api-architecture.md](./api-architecture.md) | REST + WebSocket surface, layering, sequence diagrams |
| [database-architecture.md](./database-architecture.md) | Relational schema (SQLite) for claims, decisions, disputes, audit log |
| [vector-db-architecture.md](./vector-db-architecture.md) | FAISS index design for the three RAG sources |
| [memory-architecture.md](./memory-architecture.md) | Short-term checkpointing, long-term store, dispute conversation memory |
| [security-architecture.md](./security-architecture.md) | Hybrid injection detection, PII redaction, hard-block enforcement, defense-in-depth |
| [design-decisions.md](./design-decisions.md) | Consolidated decision log — what was chosen, what was rejected, why |

Implementation status and what's still deferred (policy corpus content, tuned prompts, filled-in
test scenarios) are tracked in the root [README.md](../README.md).
