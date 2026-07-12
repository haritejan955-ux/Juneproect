"""FastAPI app factory + lifespan.

All singletons (DB engine, chat model, vector stores, compiled graph,
services) are constructed once here during ASGI startup and hung off
`app.state` — routers never construct their own dependencies, they read
them via `app.api.dependencies`. See docs/architecture.md section 3.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.graph import build_claim_graph
from app.api import websocket as websocket_router
from app.api.routers import audit, claimants, claims, decisions, disputes, health
from app.config.settings import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.llm.provider import get_chat_model
from app.memory.checkpointer import build_checkpointer
from app.memory.database import create_db_engine, init_db, make_session_factory
from app.memory.embedding_cache_store import SqlEmbeddingCacheStore
from app.memory.vector_doc_store import SqlVectorDocStore
from app.services.claim_service import ClaimService
from app.services.dispute_service import DisputeService
from app.services.streaming import StreamPublisher
from app.vectorstore.embedding_cache import CachedEmbeddings
from app.vectorstore.embeddings import get_embeddings
from app.vectorstore.hybrid_store import HybridVectorStore

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Starting up with llm_provider=%s", settings.llm_provider)

    engine = create_db_engine(settings)
    init_db(engine)
    session_factory = make_session_factory(engine)

    chat_model = get_chat_model(settings)
    embeddings = CachedEmbeddings(
        inner=get_embeddings(settings),
        store=SqlEmbeddingCacheStore(session_factory),
        model_name=settings.openai_embedding_model,
    )
    doc_store = SqlVectorDocStore(session_factory)

    policy_corpus_store = HybridVectorStore.load_or_create(
        settings.vector_index_dir, "policy_corpus", embeddings, doc_store
    )
    historical_decisions_store = HybridVectorStore.load_or_create(
        settings.vector_index_dir, "historical_decisions", embeddings, doc_store
    )

    checkpointer = build_checkpointer()

    graph = build_claim_graph(
        chat_model=chat_model,
        embeddings=embeddings,
        policy_corpus_store=policy_corpus_store,
        historical_decisions_store=historical_decisions_store,
        checkpointer=checkpointer,
        rag_top_k=settings.rag_top_k,
        rag_similarity_threshold=settings.rag_similarity_threshold,
        security_block_confidence=settings.security_block_confidence,
        self_critic_score_threshold=settings.self_critic_score_threshold,
        self_critic_max_retries=settings.self_critic_max_retries,
    )

    stream_publisher = StreamPublisher()

    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.stream_publisher = stream_publisher
    app.state.policy_corpus_store = policy_corpus_store
    app.state.historical_decisions_store = historical_decisions_store
    app.state.claim_service = ClaimService(
        graph=graph,
        session_factory=session_factory,
        upload_storage_dir=settings.upload_storage_dir,
        stream_publisher=stream_publisher,
    )
    app.state.dispute_service = DisputeService(
        chat_model=chat_model,
        session_factory=session_factory,
        policy_corpus_store=policy_corpus_store,
        rag_top_k=settings.rag_top_k,
        rag_similarity_threshold=settings.rag_similarity_threshold,
        graph=graph,
    )

    yield

    logger.info("Shutting down")


_TAGS_METADATA = [
    {
        "name": "health",
        "description": "Liveness and readiness probes. Unauthenticated — see "
        "app/api/routers/health.py.",
    },
    {"name": "claims", "description": "Submit a claim and poll its processing status."},
    {"name": "decisions", "description": "Read a claim's finalized decision."},
    {
        "name": "disputes",
        "description": "Multi-turn conversation contesting a finalized decision, including an "
        "SSE token-streaming variant.",
    },
    {"name": "audit", "description": "Full timestamped agent execution log for a claim."},
    {"name": "claimants", "description": "A claimant's prior claim history."},
]


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="US Insurance Claim Processing Agent",
        description=(
            "A multi-agent LangGraph pipeline that processes US insurance claims: parses "
            "uploaded documents, validates coverage against a policy corpus via hybrid RAG, "
            "screens for fraud and prompt injection, and produces a cited claim decision. "
            "All `/api/v1/*` routes require an `X-API-Key` header — see the security scheme "
            "below."
        ),
        version="0.1.0",
        license_info={"name": "MIT"},
        openapi_tags=_TAGS_METADATA,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Added after CORSMiddleware so it ends up outermost (Starlette wraps middleware in
    # reverse registration order) — request_id and access-log timing then cover the whole
    # request/response cycle, CORS handling included, not just the routed handler.
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(claims.router)
    app.include_router(decisions.router)
    app.include_router(disputes.router)
    app.include_router(audit.router)
    app.include_router(claimants.router)
    app.include_router(websocket_router.router)

    return app


app = create_app()
