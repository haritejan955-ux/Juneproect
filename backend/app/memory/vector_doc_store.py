"""SQLAlchemy-backed `VectorDocStore` — the persistent counterpart to
`InMemoryVectorDocStore` (used only for the ephemeral per-claim index).
Satisfies `app.vectorstore.base.VectorDocStore` without `app.vectorstore`
importing anything from `app.memory` — the dependency direction is: this
module imports the vectorstore protocol, not the other way around.

Opens a short-lived session per call rather than holding one open for the
app's lifetime: a single `Session` is not safe to share across concurrently
interleaved async requests, and this store is called from request-handling
coroutines.
"""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.memory.models import VectorDocumentRecord


class SqlVectorDocStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def put(self, index_name: str, vector_id: int, text: str, metadata: dict) -> None:
        with self._session_factory() as session:
            session.merge(
                VectorDocumentRecord(
                    index_name=index_name,
                    vector_id=vector_id,
                    text=text,
                    metadata_json=json.dumps(metadata),
                )
            )
            session.commit()

    def get(self, index_name: str, vector_id: int) -> tuple[str, dict] | None:
        with self._session_factory() as session:
            record = session.get(VectorDocumentRecord, (index_name, vector_id))
            if record is None:
                return None
            return record.text, json.loads(record.metadata_json)

    def next_id(self, index_name: str) -> int:
        with self._session_factory() as session:
            stmt = select(VectorDocumentRecord.vector_id).where(
                VectorDocumentRecord.index_name == index_name
            )
            existing_ids = session.scalars(stmt).all()
            return (max(existing_ids) + 1) if existing_ids else 0
