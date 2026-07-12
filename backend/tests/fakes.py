"""Test doubles shared across per-node unit tests.

These are real, functioning fakes — not `unittest.mock.Mock` objects — so a
test failure points at an actual behavioral mismatch (wrong prompt, wrong
call count) rather than an unconfigured mock silently returning a
`MagicMock`. Each implements only the surface a node actually calls.
"""

from collections.abc import Sequence


class FakeStructuredRunnable:
    """Stands in for `chat_model.with_structured_output(Schema)`'s return
    value. Configured with either a single canned result/exception to return
    from every `ainvoke` call, or a `list` of them to return one-per-call in
    order (repeating the last entry once exhausted) — the latter is what
    lets a test script a node's *successive* calls differently, e.g. Answer
    Synthesizer returning a low-quality draft on the first pass and a good
    one after Self-Critic sends it back for retry. A schema is only ever
    bound to one runnable at graph-construction time (see
    `MultiSchemaFakeChatModel`'s docstring), so per-call sequencing has to
    live here, not in how many runnables get created."""

    def __init__(self, result_or_exception: object) -> None:
        self._sequence: list[object] | None = (
            list(result_or_exception) if isinstance(result_or_exception, list) else None
        )
        self._single = result_or_exception if self._sequence is None else None
        self._call_count = 0
        self.prompts_received: list[str] = []

    async def ainvoke(self, prompt: str) -> object:
        self.prompts_received.append(prompt)
        if self._sequence is not None:
            index = min(self._call_count, len(self._sequence) - 1)
            value = self._sequence[index]
        else:
            value = self._single
        self._call_count += 1
        if isinstance(value, BaseException):
            raise value
        return value


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


class MultiSchemaFakeChatModel:
    """Like `FakeChatModel`, but serves a different canned result per requested schema — needed
    when a single test drives more than one node through the same `chat_model` instance (e.g. a
    full-graph run, where Intent Analyzer and Security Checker's classifier each call
    `with_structured_output` with a different schema). Raises `AssertionError` for an
    unconfigured schema rather than returning `None` — a test relying on this fake should know
    immediately if it exercised a node it didn't mean to.

    A schema's configured value may be a `list` instead of a single result/exception, in which
    case `FakeStructuredRunnable` serves it one-per-call in order — e.g.
    `{_CritiqueResult: [_CritiqueResult(...low score...), _CritiqueResult(...high score...)]}`
    to script a retry: Self-Critic fails the first pass, Answer Synthesizer runs again on the
    `prepare_retry` edge, and Self-Critic passes the second time, exercising the real
    conditional retry edge end-to-end rather than asserting on `route_after_critic` in
    isolation."""

    def __init__(self, by_schema: dict[type, object]) -> None:
        self._by_schema = by_schema
        self.runnables_by_schema: dict[type, FakeStructuredRunnable] = {}

    def with_structured_output(self, schema: type) -> FakeStructuredRunnable:
        if schema not in self._by_schema:
            raise AssertionError(
                f"MultiSchemaFakeChatModel has no configured response for {schema} — "
                f"configured schemas: {list(self._by_schema)}"
            )
        runnable = FakeStructuredRunnable(self._by_schema[schema])
        self.runnables_by_schema[schema] = runnable
        return runnable


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
