from app.vectorstore.bm25_index import BM25Index, tokenize


def test_tokenize_lowercases_and_splits_on_non_alphanumeric():
    assert tokenize("CPT 97110 — Therapeutic Exercise!") == [
        "cpt",
        "97110",
        "therapeutic",
        "exercise",
    ]


def test_empty_index_returns_no_results():
    index = BM25Index()
    assert index.search("anything", k=5) == []


def test_finds_exact_term_match():
    # 3 documents, not 2: with only 2 documents where a term appears in exactly one, BM25's IDF
    # term (log((N - n + 0.5) / (n + 0.5))) evaluates to log(1) = 0 — not a bug, just how BM25
    # behaves at that specific corpus size. A slightly larger corpus avoids that edge case.
    index = BM25Index()
    index.add_many(
        [
            (1, "CPT code 97110 is used for therapeutic exercise."),
            (2, "The claimant reported a slip and fall injury."),
            (3, "Emergency room visit for chest pain."),
        ]
    )
    results = index.search("97110", k=5)
    assert results[0][0] == 1


def test_no_term_overlap_returns_no_results():
    """BM25 scores unrelated documents as 0 — the index filters these out
    rather than returning irrelevant results just to fill k slots."""
    index = BM25Index()
    index.add_many(
        [
            (1, "CPT code 97110 is used for therapeutic exercise."),
            (2, "The claimant reported a slip and fall injury."),
        ]
    )
    results = index.search("completely unrelated aardvark zoology", k=5)
    assert results == []


def test_add_and_add_many_are_interchangeable():
    single = BM25Index()
    single.add(1, "duplicate billing detected")
    single.add(2, "upcoding detected")

    batch = BM25Index()
    batch.add_many([(1, "duplicate billing detected"), (2, "upcoding detected")])

    assert single.search("duplicate billing", k=5) == batch.search("duplicate billing", k=5)
