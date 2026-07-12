"""Unit tests for [3] RAG Retriever.

Uses real `FaissVectorStore` instances (in-memory, ephemeral) seeded with
`FakeEmbeddings` — this exercises the real merge/threshold logic, faking
only the actual external dependency (an embeddings API call).
"""

import pytest

from app.agents.nodes.rag_retriever import build_rag_retriever_node
from app.core.exceptions import VectorStoreError
from app.state.graph_state import DocumentChunk, GraphState
from app.vectorstore.faiss_store import FaissVectorStore
from tests.fakes import FakeEmbeddings


def _chunk(chunk_id: str, text: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id, text=text, section="1", doc_type="cms_1500", preserved_codes=[]
    )


async def test_merges_results_from_all_three_sources():
    # `rag_retriever` always builds its ephemeral per-claim index at the default embedding
    # dimension (see the node's docstring), so these fakes must match that dimension too.
    embeddings = FakeEmbeddings()
    policy_store = FaissVectorStore.ephemeral("policy_corpus", embeddings)
    policy_store.add_texts(
        ["ACA essential benefits cover ambulatory care."], [{"doc_title": "ACA"}]
    )
    history_store = FaissVectorStore.ephemeral("historical_decisions", embeddings)
    history_store.add_texts(["A similar claim was approved."], [{"doc_title": "history"}])

    node = build_rag_retriever_node(
        policy_corpus_store=policy_store,
        historical_decisions_store=history_store,
        embeddings=embeddings,
        top_k=5,
        similarity_threshold=-1.0,  # nothing is "low confidence" for this test
    )

    state: GraphState = {
        "claim_id": "c1",
        "query": "is ambulatory care covered",
        "chunks": [_chunk("ch1", "Patient received ambulatory care on 2026-01-01.")],
    }
    result = await node(state)

    sources = {chunk["source"] for chunk in result["retrieved_chunks"]}
    assert sources == {"claim_document", "policy_corpus", "historical_decision"}
    assert result["low_confidence_retrieval"] is False
    assert result["audit_log"][0]["action"] == "retrieved_chunks"


async def test_flags_low_confidence_without_dropping_results():
    embeddings = FakeEmbeddings()
    policy_store = FaissVectorStore.ephemeral("policy_corpus", embeddings)
    policy_store.add_texts(["some policy text"], [{"doc_title": "policy"}])
    history_store = FaissVectorStore.ephemeral("historical_decisions", embeddings)

    node = build_rag_retriever_node(
        policy_corpus_store=policy_store,
        historical_decisions_store=history_store,
        embeddings=embeddings,
        top_k=5,
        similarity_threshold=2.0,  # impossibly high threshold -> everything is low-confidence
    )

    state: GraphState = {"claim_id": "c1", "query": "anything", "chunks": []}
    result = await node(state)

    assert result["low_confidence_retrieval"] is True
    assert all(chunk["low_confidence"] for chunk in result["retrieved_chunks"])
    # Low-confidence results are flagged, not silently dropped.
    assert len(result["retrieved_chunks"]) == 1


async def test_no_results_is_also_low_confidence():
    embeddings = FakeEmbeddings()
    policy_store = FaissVectorStore.ephemeral("policy_corpus", embeddings)
    history_store = FaissVectorStore.ephemeral("historical_decisions", embeddings)

    node = build_rag_retriever_node(
        policy_corpus_store=policy_store,
        historical_decisions_store=history_store,
        embeddings=embeddings,
        top_k=5,
        similarity_threshold=0.5,
    )

    state: GraphState = {"claim_id": "c1", "query": "anything", "chunks": []}
    result = await node(state)

    assert result["retrieved_chunks"] == []
    assert result["low_confidence_retrieval"] is True


async def test_embedding_failure_raises_vector_store_error():
    embeddings = FakeEmbeddings(raise_on_call=RuntimeError("embeddings API down"))
    policy_store = FaissVectorStore.ephemeral("policy_corpus", embeddings)
    history_store = FaissVectorStore.ephemeral("historical_decisions", embeddings)

    node = build_rag_retriever_node(
        policy_corpus_store=policy_store,
        historical_decisions_store=history_store,
        embeddings=embeddings,
        top_k=5,
        similarity_threshold=0.5,
    )

    state: GraphState = {
        "claim_id": "c1",
        "query": "anything",
        "chunks": [_chunk("ch1", "some text")],
    }

    with pytest.raises(VectorStoreError) as excinfo:
        await node(state)

    assert excinfo.value.context["claim_id"] == "c1"
