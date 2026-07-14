from pathlib import Path

from app.rag.cache import EmbeddingCache


class _CountingEmbeddings:
    def __init__(self):
        self.calls = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return [[float(len(t))] for t in texts]


def test_unchanged_corpus_makes_zero_new_embedding_calls(tmp_path: Path):
    cache_path = tmp_path / "cache.json"
    embeddings = _CountingEmbeddings()
    texts = ["Warfarin and Aspirin interact.", "Digoxin and Furosemide interact."]

    cache = EmbeddingCache(cache_path)
    cache.get_or_embed(texts, embeddings)
    assert embeddings.calls == 1

    # Re-run with a fresh cache instance loaded from the same persisted file.
    reloaded_cache = EmbeddingCache(cache_path)
    reloaded_cache.get_or_embed(texts, embeddings)
    assert embeddings.calls == 1  # no new embedding calls for unchanged texts


def test_new_text_triggers_exactly_one_embedding_call_for_the_delta(tmp_path: Path):
    cache_path = tmp_path / "cache.json"
    embeddings = _CountingEmbeddings()

    cache = EmbeddingCache(cache_path)
    cache.get_or_embed(["a", "b"], embeddings)
    assert embeddings.calls == 1

    cache.get_or_embed(["a", "b", "c"], embeddings)
    assert embeddings.calls == 2
