"""Vector store abstraction.

`VectorStore` is deliberately narrow (add / search / save / load) so the
FAISS implementation can later be swapped (e.g. for Chroma) without any
agent node code changing — see docs/vector-db-architecture.md for why FAISS
was chosen at this scale.

Metadata/text for each vector lives behind the separate `VectorDocStore`
protocol rather than inside the FAISS index itself (FAISS only stores
vectors + integer ids). `app.memory.vector_doc_store.SqlVectorDocStore` is
the concrete implementation, backed by the same SQLite database as the rest
of the app's durable state — this keeps `vectorstore/` free of a dependency
on `memory/`, and the concrete wiring happens once, in the DI layer.
"""

from typing import Protocol, TypedDict


class ScoredChunk(TypedDict):
    text: str
    source: str
    score: float
    metadata: dict
    low_confidence: bool


class VectorDocStore(Protocol):
    """Text + metadata storage for vectors, keyed by (index_name, vector_id)."""

    def put(self, index_name: str, vector_id: int, text: str, metadata: dict) -> None: ...

    def get(self, index_name: str, vector_id: int) -> tuple[str, dict] | None: ...

    def next_id(self, index_name: str) -> int: ...


class VectorStore(Protocol):
    """A single named collection of embedded chunks (one FAISS index)."""

    index_name: str

    def add_texts(self, texts: list[str], metadatas: list[dict]) -> list[int]: ...

    def search(
        self, query: str, k: int, threshold: float, source_label: str
    ) -> list[ScoredChunk]: ...

    def save(self, directory: str) -> None: ...
