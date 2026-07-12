"""FAISS-backed VectorStore implementation.

Uses `IndexFlatIP` (exact cosine similarity over L2-normalized vectors)
wrapped in `IndexIDMap2` so vector ids are stable and match the companion
`VectorDocStore`'s primary keys, and so an index can grow via `add_texts`
without a full rebuild (needed for the `historical_decisions` index, which
is appended to after every finalized claim). See
docs/vector-db-architecture.md for why exact search is the right choice at
this corpus size, and the one-line upgrade path if that changes.
"""

import os

import faiss
import numpy as np
from langchain_core.embeddings import Embeddings

from app.vectorstore.base import ScoredChunk, VectorDocStore

DEFAULT_EMBEDDING_DIM = 1536


class InMemoryVectorDocStore(VectorDocStore):
    """Doc store for ephemeral, per-claim indices that are never persisted.

    See docs/vector-db-architecture.md: the per-claim index is built from
    raw, pre-redaction document content (RAG Retriever runs before Security
    Checker), so it must never touch disk.
    """

    def __init__(self) -> None:
        self._docs: dict[tuple[str, int], tuple[str, dict]] = {}
        self._counters: dict[str, int] = {}

    def put(self, index_name: str, vector_id: int, text: str, metadata: dict) -> None:
        self._docs[(index_name, vector_id)] = (text, metadata)

    def get(self, index_name: str, vector_id: int) -> tuple[str, dict] | None:
        return self._docs.get((index_name, vector_id))

    def next_id(self, index_name: str) -> int:
        current = self._counters.get(index_name, 0)
        self._counters[index_name] = current + 1
        return current

    def get_all(self, index_name: str) -> list[tuple[int, str, dict]]:
        return [
            (vector_id, text, metadata)
            for (name, vector_id), (text, metadata) in self._docs.items()
            if name == index_name
        ]


class FaissVectorStore:
    index_name: str

    def __init__(
        self,
        index_name: str,
        embeddings: Embeddings,
        doc_store: VectorDocStore,
        dimension: int = DEFAULT_EMBEDDING_DIM,
    ) -> None:
        self.index_name = index_name
        self._embeddings = embeddings
        self._doc_store = doc_store
        self._dimension = dimension
        self._index = faiss.IndexIDMap2(faiss.IndexFlatIP(dimension))

    def add_texts(self, texts: list[str], metadatas: list[dict]) -> list[int]:
        if not texts:
            return []
        vectors = np.array(self._embeddings.embed_documents(texts), dtype="float32")
        faiss.normalize_L2(vectors)

        ids: list[int] = []
        for text, metadata in zip(texts, metadatas, strict=True):
            vector_id = self._doc_store.next_id(self.index_name)
            self._doc_store.put(self.index_name, vector_id, text, metadata)
            ids.append(vector_id)

        self._index.add_with_ids(vectors, np.array(ids, dtype="int64"))
        return ids

    def search_ids(self, query: str, k: int) -> list[tuple[int, float]]:
        """Raw ranked (vector_id, cosine_similarity) pairs, best-first, with
        no doc-store lookup and no threshold applied. This is the primitive
        `search()` builds on, and what `HybridVectorStore` fuses with BM25's
        ranking via Reciprocal Rank Fusion — see vectorstore/fusion.py."""
        if self._index.ntotal == 0:
            return []

        query_vector = np.array([self._embeddings.embed_query(query)], dtype="float32")
        faiss.normalize_L2(query_vector)

        scores, vector_ids = self._index.search(query_vector, min(k, self._index.ntotal))

        return [
            (int(vector_id), float(score))
            for score, vector_id in zip(scores[0], vector_ids[0], strict=True)
            if vector_id != -1
        ]

    def search(
        self, query: str, k: int, threshold: float, source_label: str
    ) -> list[ScoredChunk]:
        results: list[ScoredChunk] = []
        for vector_id, score in self.search_ids(query, k):
            doc = self._doc_store.get(self.index_name, vector_id)
            if doc is None:
                continue
            text, metadata = doc
            results.append(
                ScoredChunk(
                    text=text,
                    source=source_label,
                    score=score,
                    metadata=metadata,
                    low_confidence=score < threshold,
                )
            )
        return results

    def save(self, directory: str) -> None:
        os.makedirs(directory, exist_ok=True)
        faiss.write_index(self._index, os.path.join(directory, f"{self.index_name}.faiss"))

    @classmethod
    def load_or_create(
        cls,
        directory: str,
        index_name: str,
        embeddings: Embeddings,
        doc_store: VectorDocStore,
        dimension: int = DEFAULT_EMBEDDING_DIM,
    ) -> "FaissVectorStore":
        store = cls(index_name, embeddings, doc_store, dimension)
        path = os.path.join(directory, f"{index_name}.faiss")
        if os.path.exists(path):
            store._index = faiss.read_index(path)
        return store

    @classmethod
    def ephemeral(
        cls, index_name: str, embeddings: Embeddings, dimension: int = DEFAULT_EMBEDDING_DIM
    ) -> "FaissVectorStore":
        return cls(index_name, embeddings, InMemoryVectorDocStore(), dimension)
