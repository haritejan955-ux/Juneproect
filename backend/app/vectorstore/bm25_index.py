"""Sparse (BM25) keyword index — the other half of hybrid retrieval.

Dense embeddings are strong at semantic similarity but weak at exact-term
matches: a CPT code like "97110", a statute number like "10 CCR §2695", or
an uncommon proper noun can end up diluted in a dense vector alongside the
surrounding prose. BM25 is the reverse — exact/near-exact term overlap,
no semantic understanding. Combining both (see fusion.py) covers more
query types than either alone. See docs/vector-db-architecture.md.
"""

import re

from rank_bm25 import BM25Okapi

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


class BM25Index:
    """In-memory only — never persisted to disk. Rebuilt at startup from
    `VectorDocStore.get_all()` (see `HybridVectorStore.load_or_create`),
    since the source texts are already durably stored there; serializing a
    second copy of the same corpus into a BM25-specific format would be
    redundant storage for no benefit at this corpus size.
    """

    def __init__(self) -> None:
        self._ids: list[int] = []
        self._tokenized_corpus: list[list[str]] = []
        self._bm25: BM25Okapi | None = None

    def add(self, vector_id: int, text: str) -> None:
        self._ids.append(vector_id)
        self._tokenized_corpus.append(tokenize(text))
        # rank_bm25 has no incremental-add API — the index is rebuilt from the accumulated
        # corpus on every add. O(n) per add is fine at this corpus's scale (see module
        # docstring); a corpus large enough for this to matter would batch adds instead of
        # rebuilding after each one.
        self._bm25 = BM25Okapi(self._tokenized_corpus)

    def add_many(self, items: list[tuple[int, str]]) -> None:
        for vector_id, text in items:
            self._ids.append(vector_id)
            self._tokenized_corpus.append(tokenize(text))
        if self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)

    def search(self, query: str, k: int) -> list[tuple[int, float]]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self._ids, scores, strict=True), key=lambda pair: pair[1], reverse=True)
        return [(vector_id, float(score)) for vector_id, score in ranked[:k] if score > 0]
