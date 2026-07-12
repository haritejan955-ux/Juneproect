"""[3] RAG Retriever — searches all three required sources, merges with
source metadata attached, flags low-confidence matches instead of dropping
them. See docs/vector-db-architecture.md section 4.

The per-claim index is built fresh, in-memory, on every run
(`FaissVectorStore.ephemeral`) — it is never persisted, since this node
runs before Security Checker's PII redaction pass.
"""

from collections.abc import Awaitable, Callable

from langchain_core.embeddings import Embeddings

from app.core.audit import audit_update
from app.state.graph_state import GraphState, RetrievedChunk
from app.vectorstore.base import VectorStore
from app.vectorstore.faiss_store import FaissVectorStore

AGENT_NAME = "rag_retriever"


def build_rag_retriever_node(
    policy_corpus_store: VectorStore,
    historical_decisions_store: VectorStore,
    embeddings: Embeddings,
    top_k: int,
    similarity_threshold: float,
) -> Callable[[GraphState], Awaitable[dict]]:
    async def rag_retriever(state: GraphState) -> dict:
        query = state["query"]
        chunks = state.get("chunks", [])

        per_claim_store = FaissVectorStore.ephemeral("per_claim", embeddings)
        if chunks:
            per_claim_store.add_texts(
                texts=[chunk["text"] for chunk in chunks],
                metadatas=[
                    {"section": chunk["section"], "doc_type": chunk["doc_type"]} for chunk in chunks
                ],
            )

        results: list[RetrievedChunk] = []
        for store, source_label in (
            (per_claim_store, "claim_document"),
            (policy_corpus_store, "policy_corpus"),
            (historical_decisions_store, "historical_decision"),
        ):
            for scored in store.search(query, top_k, similarity_threshold, source_label):
                results.append(
                    RetrievedChunk(
                        text=scored["text"],
                        source=scored["source"],  # type: ignore[typeddict-item]
                        score=scored["score"],
                        section=scored["metadata"].get("section"),
                        doc_title=scored["metadata"].get("doc_title"),
                        low_confidence=scored["low_confidence"],
                    )
                )

        low_confidence_retrieval = (not results) or any(r["low_confidence"] for r in results)

        return {
            "retrieved_chunks": results,
            "low_confidence_retrieval": low_confidence_retrieval,
            **audit_update(
                AGENT_NAME,
                "retrieved_chunks",
                {"result_count": len(results), "low_confidence": low_confidence_retrieval},
            ),
        }

    return rag_retriever
