"""Deterministic fakes so every test — including full-pipeline ones — runs without a
live LLM or embeddings API call."""

from typing import Any

from langchain_core.embeddings import Embeddings

from app.data.drug_reference import DRUG_REFERENCE

_VOCAB = [record["canonical_name"].lower() for record in DRUG_REFERENCE.values()] + [
    "interaction",
    "allergy",
    "renal",
    "impairment",
    "diuretic",
]


class FakeEmbeddings(Embeddings):
    """Bag-of-drug-name-mentions embedding: two texts mentioning the same drugs land
    close together, which is all InteractionRetriever's membership-checked search needs."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)

    @staticmethod
    def _vec(text: str) -> list[float]:
        lowered = text.lower()
        return [float(lowered.count(word)) for word in _VOCAB]


class _FakeStructuredRunnable:
    def __init__(self, queues: dict[type, list[Any]], schema: type):
        self._queues = queues
        self._schema = schema

    def invoke(self, messages: Any) -> Any:
        queue = self._queues.get(self._schema)
        if not queue:
            raise AssertionError(f"FakeChatModel: no queued response for {self._schema.__name__}")
        return queue.pop(0)


class FakeChatModel:
    """Queue canned structured-output responses per Pydantic schema, FIFO. Duck-types
    the `.with_structured_output(schema).invoke(messages)` surface every node actually
    calls — no need to satisfy the full BaseChatModel abstract interface."""

    def __init__(self) -> None:
        self._queues: dict[type, list[Any]] = {}

    def queue(self, response: Any) -> "FakeChatModel":
        self._queues.setdefault(type(response), []).append(response)
        return self

    def with_structured_output(self, schema: type) -> _FakeStructuredRunnable:
        return _FakeStructuredRunnable(self._queues, schema)
