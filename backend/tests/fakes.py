"""Test doubles shared across per-node unit tests.

These are real, functioning fakes — not `unittest.mock.Mock` objects — so a
test failure points at an actual behavioral mismatch (wrong prompt, wrong
call count) rather than an unconfigured mock silently returning a
`MagicMock`. Each implements only the surface a node actually calls.
"""

from collections.abc import Sequence


class FakeStructuredRunnable:
    """Stands in for `chat_model.with_structured_output(Schema)`'s return
    value. Configured with either a canned result to return from `ainvoke`,
    or an exception instance to raise — covers both the happy path and the
    error-handling path every node's unit tests need."""

    def __init__(self, result_or_exception: object) -> None:
        self._result_or_exception = result_or_exception
        self.prompts_received: list[str] = []

    async def ainvoke(self, prompt: str) -> object:
        self.prompts_received.append(prompt)
        if isinstance(self._result_or_exception, BaseException):
            raise self._result_or_exception
        return self._result_or_exception


class FakeChatModel:
    """Stands in for `langchain_core.language_models.BaseChatModel`. Every
    node only ever calls `.with_structured_output(...)`, so that's the only
    method implemented. `last_runnable` lets a test assert on what prompt
    was actually built and sent, without a real LLM call."""

    def __init__(self, result_or_exception: object) -> None:
        self._result_or_exception = result_or_exception
        self.last_runnable: FakeStructuredRunnable | None = None
        self.schemas_requested: list[type] = []

    def with_structured_output(self, schema: type) -> FakeStructuredRunnable:
        self.schemas_requested.append(schema)
        self.last_runnable = FakeStructuredRunnable(self._result_or_exception)
        return self.last_runnable

    async def ainvoke(self, prompt: str) -> object:
        """Some nodes (dispute_responder) call the chat model directly,
        without structured output — a plain message-like object back."""
        if isinstance(self._result_or_exception, BaseException):
            raise self._result_or_exception
        return self._result_or_exception


class FakeEmbeddings:
    """Deterministic, dependency-free stand-in for `langchain_core.embeddings.Embeddings`.
    Returns a fixed-dimension vector derived from a hash of the input text — these tests
    exercise wiring and error handling, not retrieval quality, so vectors don't need to encode
    real semantic similarity."""

    def __init__(self, dimension: int = 1536, raise_on_call: BaseException | None = None) -> None:
        self._dimension = dimension
        self._raise_on_call = raise_on_call
        # Tracks every text actually sent through — lets a test assert that a caching layer
        # in front of this fake avoided a redundant call, not just that it returned the right
        # vector (which a broken cache that fell through to the wrapped embeddings every time
        # would also do).
        self.embed_documents_calls: list[list[str]] = []
        self.embed_query_calls: list[str] = []

    def _vector(self, text: str) -> list[float]:
        if self._raise_on_call is not None:
            raise self._raise_on_call
        seed = sum(ord(c) for c in text) or 1
        return [((seed * (i + 1)) % 97) / 97.0 for i in range(self._dimension)]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        self.embed_documents_calls.append(list(texts))
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        self.embed_query_calls.append(text)
        return self._vector(text)


class FakeEmbeddingCacheStore:
    """In-memory stand-in for `app.memory.embedding_cache_store.SqlEmbeddingCacheStore` —
    same `get`/`put` surface, no database."""

    def __init__(self) -> None:
        self._entries: dict[str, list[float]] = {}
        self.put_calls: list[tuple[str, str]] = []

    def get(self, key: str) -> list[float] | None:
        return self._entries.get(key)

    def put(self, key: str, model_name: str, embedding: list[float]) -> None:
        self._entries[key] = embedding
        self.put_calls.append((key, model_name))
