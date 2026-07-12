"""Hybrid (dense + sparse) retrieval — the production `VectorStore`
implementation used everywhere `FaissVectorStore` used to be used directly.

Composes a `FaissVectorStore` (dense, cosine similarity) and a `BM25Index`
(sparse, keyword) over the *same* corpus, merges their rankings with
Reciprocal Rank Fusion (see fusion.py), and reports each result's
similarity for threshold/low-confidence purposes using its **dense** score
specifically — not the fused RRF score. This is a deliberate choice: the
configurable `similarity_threshold` (docs/vector-db-architecture.md) is
calibrated in cosine-similarity terms (roughly 0-1), which RRF scores are
not comparable to. A chunk surfaced only by the BM25 side (no dense score
at all) is treated as `dense_score = 0.0` — i.e. flagged low-confidence —
since "found only by exact keyword match, not by semantic similarity" is
exactly the situation that flag exists to surface.
"""

import os

import faiss
from langchain_core.embeddings import Embeddings

from app.core.logging import get_logger
from app.vectorstore.base import ScoredChunk, VectorDocStore
from app.vectorstore.bm25_index import BM25Index
from app.vectorstore.faiss_store import (
    DEFAULT_EMBEDDING_DIM,
    FaissVectorStore,
    InMemoryVectorDocStore,
)
from app.vectorstore.fusion import reciprocal_rank_fusion

logger = get_logger(__name__)

OVERFETCH_MULTIPLIER = 4
"""Each side (dense, sparse) is asked for `k * OVERFETCH_MULTIPLIER` candidates before fusion,
so RRF has enough material from both rankings to actually change the outcome — fusing two
already-truncated top-k lists tends to just reproduce the dense-only ranking."""


class HybridVectorStore:
    index_name: str

    def __init__(
        self,
        index_name: str,
        embeddings: Embeddings,
        doc_store: VectorDocStore,
        dimension: int = DEFAULT_EMBEDDING_DIM,
    ) -> None:
        self.index_name = index_name
        self._dense = FaissVectorStore(index_name, embeddings, doc_store, dimension)
        self._sparse = BM25Index()
        self._doc_store = doc_store

    def add_texts(self, texts: list[str], metadatas: list[dict]) -> list[int]:
        if not texts:
            return []
        ids = self._dense.add_texts(texts, metadatas)
        self._sparse.add_many(list(zip(ids, texts, strict=True)))
        return ids

    def search(
        self, query: str, k: int, threshold: float, source_label: str
    ) -> list[ScoredChunk]:
        overfetch_k = k * OVERFETCH_MULTIPLIER
        dense_ranked = self._dense.search_ids(query, overfetch_k)
        sparse_ranked = self._sparse.search(query, overfetch_k)
        dense_scores_by_id = dict(dense_ranked)

        fused = reciprocal_rank_fusion(dense_ranked, sparse_ranked)[:k]

        logger.info(
            "hybrid_store.search",
            extra={
                "index_name": self.index_name,
                "dense_candidates": len(dense_ranked),
                "sparse_candidates": len(sparse_ranked),
                "fused_results": len(fused),
            },
        )

        results: list[ScoredChunk] = []
        for vector_id, _fused_score in fused:
            doc = self._doc_store.get(self.index_name, vector_id)
            if doc is None:
                continue
            text, metadata = doc
            dense_score = dense_scores_by_id.get(vector_id, 0.0)
            results.append(
                ScoredChunk(
                    text=text,
                    source=source_label,
                    score=dense_score,
                    metadata=metadata,
                    low_confidence=dense_score < threshold,
                )
            )
        return results

    def search_dense_only(
        self, query: str, k: int, threshold: float, source_label: str
    ) -> list[ScoredChunk]:
        """Bypasses fusion — dense retrieval alone, using the same underlying index and doc
        store as `search()`. Not used by any production code path; exists for
        `scripts/evaluate_retrieval.py` to report the hybrid-vs-dense-only comparison that
        justifies hybrid retrieval being the default."""
        return self._dense.search(query, k, threshold, source_label)

    def document_count(self) -> int:
        """Dense-index count — used by the `/health/ready` readiness check to confirm an
        index actually loaded, not to reflect BM25 state (the two always hold the same
        documents by construction, see `add_texts`/`load_or_create`)."""
        return self._dense.document_count()

    def save(self, directory: str) -> None:
        # BM25 is deliberately not persisted — see the class docstring and BM25Index's.
        self._dense.save(directory)

    @classmethod
    def load_or_create(
        cls,
        directory: str,
        index_name: str,
        embeddings: Embeddings,
        doc_store: VectorDocStore,
        dimension: int = DEFAULT_EMBEDDING_DIM,
    ) -> "HybridVectorStore":
        store = cls(index_name, embeddings, doc_store, dimension)
        path = os.path.join(directory, f"{index_name}.faiss")
        if os.path.exists(path):
            store._dense._index = faiss.read_index(path)
            existing = doc_store.get_all(index_name)
            store._sparse.add_many(
                [(vector_id, text) for vector_id, text, _metadata in existing]
            )
            logger.info(
                "hybrid_store.loaded",
                extra={"index_name": index_name, "vector_count": len(existing)},
            )
        return store

    @classmethod
    def ephemeral(
        cls, index_name: str, embeddings: Embeddings, dimension: int = DEFAULT_EMBEDDING_DIM
    ) -> "HybridVectorStore":
        return cls(index_name, embeddings, InMemoryVectorDocStore(), dimension)
