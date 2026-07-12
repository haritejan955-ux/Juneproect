"""Unit tests for CachedEmbeddings — asserting actual call avoidance, not
just correct return values (a broken cache that never hits would still
return correct vectors, just slower and more expensively)."""

from app.vectorstore.embedding_cache import CachedEmbeddings, cache_key
from tests.fakes import FakeEmbeddingCacheStore, FakeEmbeddings


def test_cache_key_differs_by_model_name_for_identical_text():
    """Two models must never share a cache entry for the same text — their
    vectors are not interchangeable."""
    key_a = cache_key("model-a", "hello world")
    key_b = cache_key("model-b", "hello world")
    assert key_a != key_b


def test_cache_key_is_stable_for_identical_input():
    assert cache_key("model-a", "hello world") == cache_key("model-a", "hello world")


def test_embed_query_second_call_hits_cache_not_inner():
    inner = FakeEmbeddings()
    cache = CachedEmbeddings(inner, FakeEmbeddingCacheStore(), model_name="test-model")

    first = cache.embed_query("What is covered under my policy?")
    second = cache.embed_query("What is covered under my policy?")

    assert first == second
    assert len(inner.embed_query_calls) == 1  # not called again on the second, identical query


def test_embed_query_persists_to_the_backing_store():
    store = FakeEmbeddingCacheStore()
    inner = FakeEmbeddings()
    cache = CachedEmbeddings(inner, store, model_name="test-model")

    cache.embed_query("some text")

    assert len(store.put_calls) == 1


def test_persistent_store_hit_avoids_inner_call_even_on_a_fresh_wrapper():
    """The whole point of the *persistent* tier: a second `CachedEmbeddings` instance (e.g. a
    new process) sharing the same backing store must still get a cache hit, not just the
    in-process dict tier."""
    store = FakeEmbeddingCacheStore()
    inner_first = FakeEmbeddings()
    CachedEmbeddings(inner_first, store, model_name="test-model").embed_query("some text")

    inner_second = FakeEmbeddings()
    cache_second = CachedEmbeddings(inner_second, store, model_name="test-model")
    cache_second.embed_query("some text")

    assert inner_second.embed_query_calls == []


def test_embed_documents_only_calls_inner_for_cache_misses():
    inner = FakeEmbeddings()
    cache = CachedEmbeddings(inner, FakeEmbeddingCacheStore(), model_name="test-model")

    cache.embed_documents(["doc A", "doc B"])
    inner.embed_documents_calls.clear()

    # doc A repeats, doc C is new — only doc C should reach the inner embeddings.
    cache.embed_documents(["doc A", "doc C"])

    assert inner.embed_documents_calls == [["doc C"]]


def test_embed_documents_preserves_order_and_alignment():
    inner = FakeEmbeddings()
    cache = CachedEmbeddings(inner, FakeEmbeddingCacheStore(), model_name="test-model")

    cache.embed_documents(["doc A", "doc B"])  # prime the cache for doc A and doc B
    results = cache.embed_documents(["doc B", "doc C", "doc A"])

    assert results[0] == inner._vector("doc B")
    assert results[1] == inner._vector("doc C")
    assert results[2] == inner._vector("doc A")


def test_different_models_do_not_share_cached_vectors():
    store = FakeEmbeddingCacheStore()
    inner_a = FakeEmbeddings()
    inner_b = FakeEmbeddings()
    cache_a = CachedEmbeddings(inner_a, store, model_name="model-a")
    cache_b = CachedEmbeddings(inner_b, store, model_name="model-b")

    cache_a.embed_query("shared text")
    cache_b.embed_query("shared text")

    # Both inner embeddings were called — model-b's cache miss was not served by model-a's entry.
    assert inner_a.embed_query_calls == ["shared text"]
    assert inner_b.embed_query_calls == ["shared text"]
