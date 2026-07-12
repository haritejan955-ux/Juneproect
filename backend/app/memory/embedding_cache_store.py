"""SQLAlchemy-backed `EmbeddingCacheStore` — the persistent tier of
`app.vectorstore.embedding_cache.CachedEmbeddings`. Same short-lived-session
pattern as `SqlVectorDocStore`; see that module's docstring for why.
"""

import json

from sqlalchemy.orm import Session, sessionmaker

from app.memory.models import EmbeddingCacheRecord


class SqlEmbeddingCacheStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get(self, key: str) -> list[float] | None:
        with self._session_factory() as session:
            record = session.get(EmbeddingCacheRecord, key)
            if record is None:
                return None
            return json.loads(record.embedding_json)

    def put(self, key: str, model_name: str, embedding: list[float]) -> None:
        with self._session_factory() as session:
            session.merge(
                EmbeddingCacheRecord(
                    cache_key=key,
                    model_name=model_name,
                    embedding_json=json.dumps(embedding),
                )
            )
            session.commit()
