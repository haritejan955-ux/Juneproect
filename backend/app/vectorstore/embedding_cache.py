"""Persistent embedding cache — avoids re-calling the embeddings API for
text that's already been embedded. Ingestion re-runs (incremental
indexing, see scripts/build_policy_index.py), repeated evaluation-script
runs, and identical text recurring across claims/disputes within a
session all benefit; the cost/latency saving compounds every time the
same chunk text is embedded twice.
"""

import hashlib
from typing import Protocol

from langchain_core.embeddings import Embeddings

from app.core.logging import get_logger

logger = get_logger(__name__)


def cache_key(model_name: str, text: str) -> str:
    """SHA-256 of (model_name, text). The model name is part of the key
    because different embedding models produce different, non-comparable
    vectors for identical text — a cache hit must never serve a vector
    computed by the wrong model."""
    digest = hashlib.sha256()
    digest.update(model_name.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()


class EmbeddingCacheStore(Protocol):
    """Persistence tier only — no in-memory logic here. See
    `app.memory.embedding_cache_store.SqlEmbeddingCacheStore` for the
    concrete implementation."""

    def get(self, key: str) -> list[float] | None: ...

    def put(self, key: str, model_name: str, embedding: list[float]) -> None: ...


class CachedEmbeddings(Embeddings):
    """Wraps a real `Embeddings` implementation with a two-tier cache: an
    in-process dict (fastest, cleared on restart) in front of a persistent
    `EmbeddingCacheStore` (survives restarts, shared across ingestion runs
    and requests). Every call returns exactly what the wrapped
    implementation would have returned — this is purely a cost/latency
    optimization, never a behavior change."""

    def __init__(self, inner: Embeddings, store: EmbeddingCacheStore, model_name: str) -> None:
        self._inner = inner
        self._store = store
        self._model_name = model_name
        self._memory_cache: dict[str, list[float]] = {}

    def _get_cached(self, text: str) -> list[float] | None:
        key = cache_key(self._model_name, text)
        if key in self._memory_cache:
            return self._memory_cache[key]
        cached = self._store.get(key)
        if cached is not None:
            self._memory_cache[key] = cached
        return cached

    def _store_result(self, text: str, embedding: list[float]) -> None:
        key = cache_key(self._model_name, text)
        self._memory_cache[key] = embedding
        self._store.put(key, self._model_name, embedding)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float] | None] = [self._get_cached(text) for text in texts]
        missing_indices = [i for i, cached in enumerate(results) if cached is None]

        if missing_indices:
            fresh_embeddings = self._inner.embed_documents([texts[i] for i in missing_indices])
            for index, embedding in zip(missing_indices, fresh_embeddings, strict=True):
                self._store_result(texts[index], embedding)
                results[index] = embedding

        logger.info(
            "embedding_cache.embed_documents",
            extra={
                "requested": len(texts),
                "cache_hits": len(texts) - len(missing_indices),
                "cache_misses": len(missing_indices),
            },
        )
        # Every index was either a cache hit above or filled in the loop — none remain None.
        return results  # type: ignore[return-value]

    def embed_query(self, text: str) -> list[float]:
        cached = self._get_cached(text)
        if cached is not None:
            logger.info("embedding_cache.embed_query", extra={"cache_hit": True})
            return cached
        embedding = self._inner.embed_query(text)
        self._store_result(text, embedding)
        logger.info("embedding_cache.embed_query", extra={"cache_hit": False})
        return embedding
