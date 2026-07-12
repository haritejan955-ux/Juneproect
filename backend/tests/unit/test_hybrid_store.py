"""Unit tests for HybridVectorStore — the production dense+sparse retrieval
implementation. Uses FakeEmbeddings (deterministic, non-semantic) since
these tests are about the fusion/merge/persistence mechanics, not
retrieval quality against real embeddings (that's scripts/evaluate_retrieval.py's job,
run against a real embeddings API)."""

from pathlib import Path

from app.vectorstore.faiss_store import InMemoryVectorDocStore
from app.vectorstore.hybrid_store import HybridVectorStore
from tests.fakes import FakeEmbeddings


def test_keyword_match_is_promoted_even_with_noisy_dense_scores():
    """The scenario hybrid retrieval exists for: a document sharing an exact,
    distinctive term with the query (a CPT code) should rank at or near the
    top even though FakeEmbeddings' dense similarity is content-blind noise."""
    embeddings = FakeEmbeddings()
    store = HybridVectorStore.ephemeral("test", embeddings)
    store.add_texts(
        texts=[
            "ACA essential health benefits include ambulatory care and emergency services.",
            "CPT code 97110 is used for therapeutic exercise procedures.",
            "The claimant reported a slip and fall injury at a grocery store.",
        ],
        metadatas=[{"doc_title": "ACA"}, {"doc_title": "CPT Guide"}, {"doc_title": "Incident"}],
    )

    results = store.search("what is CPT 97110", k=3, threshold=0.0, source_label="policy_corpus")

    assert results[0]["metadata"]["doc_title"] == "CPT Guide"


def test_search_on_empty_store_returns_no_results():
    embeddings = FakeEmbeddings()
    store = HybridVectorStore.ephemeral("test", embeddings)

    assert store.search("anything", k=5, threshold=0.5, source_label="policy_corpus") == []


def test_low_confidence_is_based_on_dense_score_not_fused_score():
    """A chunk found only via BM25 (no meaningful dense similarity) must be
    flagged low_confidence — the fused RRF score is not on a comparable
    scale to the configured similarity threshold, so it must never be used
    for that flag. See the module docstring for the full rationale."""
    embeddings = FakeEmbeddings()
    store = HybridVectorStore.ephemeral("test", embeddings)
    store.add_texts(
        texts=["some policy text about coverage"],
        metadatas=[{"doc_title": "policy"}],
    )

    # Threshold of 2.0 is higher than any possible cosine similarity (max 1.0) — everything
    # must be flagged low-confidence regardless of how well BM25 ranked it.
    results = store.search("policy coverage text", k=5, threshold=2.0, source_label="policy_corpus")
    assert all(r["low_confidence"] for r in results)


def test_save_and_load_or_create_round_trips_dense_index_and_rebuilds_sparse(tmp_path: Path):
    embeddings = FakeEmbeddings()
    # A doc store instance shared across two separate HybridVectorStore objects, simulating what
    # SqlVectorDocStore provides in production (a doc store outliving any single store object).
    doc_store = InMemoryVectorDocStore()

    store = HybridVectorStore("policy_corpus", embeddings, doc_store)
    store.add_texts(
        texts=["CPT code 97110 is used for therapeutic exercise procedures."],
        metadatas=[{"doc_title": "CPT Guide"}],
    )
    store.save(str(tmp_path))

    reloaded = HybridVectorStore.load_or_create(
        str(tmp_path), "policy_corpus", embeddings, doc_store
    )

    # The dense index was persisted to disk and reloaded; the sparse index was rebuilt in-memory
    # from doc_store.get_all() — both must produce the same search behavior as the original.
    results = reloaded.search("CPT 97110", k=1, threshold=0.0, source_label="policy_corpus")
    assert len(results) == 1
    assert results[0]["metadata"]["doc_title"] == "CPT Guide"


def test_load_or_create_with_no_persisted_index_starts_empty(tmp_path: Path):
    embeddings = FakeEmbeddings()
    doc_store = InMemoryVectorDocStore()

    store = HybridVectorStore.load_or_create(
        str(tmp_path), "policy_corpus", embeddings, doc_store
    )

    assert store.search("anything", k=5, threshold=0.0, source_label="policy_corpus") == []


def test_document_count_reflects_the_dense_index_not_bm25():
    """`/health/ready` (app/api/routers/health.py) reports this count as its readiness signal
    for each index — it must reflect documents actually added, not stay pinned at zero."""
    embeddings = FakeEmbeddings()
    store = HybridVectorStore.ephemeral("policy_corpus", embeddings)
    assert store.document_count() == 0

    store.add_texts(
        texts=["first policy excerpt", "second policy excerpt"],
        metadatas=[{"doc_title": "a"}, {"doc_title": "b"}],
    )

    assert store.document_count() == 2
