import hashlib
import json
from pathlib import Path

from langchain_core.embeddings import Embeddings

from app.core.logging import get_logger

logger = get_logger(__name__)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class EmbeddingCache:
    """Content-hash-keyed embedding cache persisted as JSON.

    Re-embedding an unchanged corpus makes zero new embedding-API calls: only
    texts whose hash isn't already in the cache get sent to the embeddings client.
    """

    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self._data: dict[str, list[float]] = {}
        if cache_path.exists():
            self._data = json.loads(cache_path.read_text(encoding="utf-8"))

    def get_or_embed(self, texts: list[str], embeddings: Embeddings) -> list[list[float]]:
        hashes = [_hash(t) for t in texts]
        missing_idx = [i for i, h in enumerate(hashes) if h not in self._data]

        if missing_idx:
            missing_texts = [texts[i] for i in missing_idx]
            new_vectors = embeddings.embed_documents(missing_texts)
            for i, vector in zip(missing_idx, new_vectors, strict=True):
                self._data[hashes[i]] = vector
            logger.info(
                "embedding_cache_miss",
                extra={"detail": {"new_embeddings": len(missing_idx), "total": len(texts)}},
            )
        else:
            logger.info(
                "embedding_cache_hit", extra={"detail": {"reused_embeddings": len(texts)}}
            )

        self._save()
        return [self._data[h] for h in hashes]

    def _save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self._data), encoding="utf-8")
