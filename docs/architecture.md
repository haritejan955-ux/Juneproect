# Architecture Overview

## Tech stack

| Layer | Choice |
|---|---|
| Agent orchestration | LangGraph `StateGraph` (Python) |
| LLM | OpenAI or Anthropic, switchable via `LLM_PROVIDER` |
| Backend API | FastAPI (async), SQLAlchemy 2.0 (async, SQLite) |
| Vector store | FAISS, via `langchain-community`, OpenAI embeddings |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + React Router |
| Tests | pytest (backend), Vitest + Testing Library (frontend) |

## Folder structure

```
.
├── backend/
│   ├── app/
│   │   ├── agents/            9 LangGraph nodes + graph wiring + routing
│   │   │   └── nodes/
│   │   ├── api/routes/        FastAPI routers (reports, health)
│   │   ├── core/               config, logging, auth, llm factory, middleware
│   │   ├── data/                drug reference table + interaction monograph corpus
│   │   ├── db/                  SQLAlchemy models + session
│   │   ├── prompts/            system prompts, one per LLM-backed node
│   │   ├── rag/                  FAISS store, embedding cache, corpus loader
│   │   ├── schemas/             Pydantic models (LLM structured output + API I/O)
│   │   ├── security/            prompt-injection detector
│   │   ├── services/            graph runner, progress broadcaster, report processor
│   │   └── state/               GraphState TypedDict
│   ├── scripts/                 build_interaction_index.py
│   └── tests/                   unit / langgraph / integration / security
├── frontend/
│   └── src/
│       ├── pages/                Submit, Processing, Report, History
│       ├── components/          SeverityBadge, FindingsList
│       ├── hooks/                 useReportProgress (WebSocket)
│       └── lib/                    typed API client
├── docker/                       Dockerfiles for both services
├── docs/                          this directory
└── docker-compose.yml
```

## Component diagram

```
┌────────────┐     REST + WebSocket      ┌───────────────────┐
│  Frontend  │ ────────────────────────▶ │   FastAPI backend  │
│ (React)    │ ◀──────────────────────── │                     │
└────────────┘                            │  ┌───────────────┐  │
                                           │  │ LangGraph      │  │
                                           │  │ safety graph   │  │
                                           │  │ (9 agents)     │  │
                                           │  └───────┬───────┘  │
                                           │          │           │
                                           │  ┌───────▼───────┐  │
                                           │  │ FAISS store    │  │
                                           │  │ (interaction   │  │
                                           │  │  monographs)   │  │
                                           │  └───────────────┘  │
                                           │  ┌───────────────┐  │
                                           │  │ SQLite (patients,│ │
                                           │  │ reports, audit)  │ │
                                           │  └───────────────┘  │
                                           └───────────────────┘
```

See the other files in this directory for the agent pipeline, API surface, database
schema, RAG design, security model, and the reasoning behind each of those choices.
