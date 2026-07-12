"""Reciprocal Rank Fusion — combines multiple independently-ranked result
lists (dense cosine similarity, sparse BM25) into one fused ranking.

RRF needs only each list's rank order, not a comparable score scale — this
is exactly why it's the standard fusion method for dense+sparse hybrid
retrieval: dense cosine similarity (bounded, roughly 0-1) and BM25 scores
(unbounded, corpus-size-dependent) cannot be meaningfully averaged or
compared directly, but their *rankings* can always be merged. See Cormack,
Clarke & Buettcher, "Reciprocal Rank Fusion Outperforms Condorcet and
Individual Rank Learning Methods" (SIGIR 2009).
"""

DEFAULT_RRF_K = 60
"""The constant from the original RRF paper. Larger k flattens the fusion
(top-ranked results across lists matter less relative to the rest);
smaller k makes fusion more winner-take-all. 60 is the paper's own
recommendation and the value most hybrid-search implementations default
to — not tuned against this project's corpus, since there's no labeled
retrieval dataset to tune it against yet (see scripts/evaluate_retrieval.py
for the harness that would make tuning possible)."""


def reciprocal_rank_fusion(
    *rankings: list[tuple[int, float]], k: int = DEFAULT_RRF_K
) -> list[tuple[int, float]]:
    """Merge any number of `(id, score)` rankings (each sorted best-first,
    score is only used to establish that ordering — not read here) into a
    single fused ranking, sorted best-first by fused score.

    `fused_score(id) = sum over every ranking containing id of 1 / (k + rank + 1)`
    """
    fused_scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, (item_id, _original_score) in enumerate(ranking):
            fused_scores[item_id] = fused_scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)

    return sorted(fused_scores.items(), key=lambda pair: pair[1], reverse=True)
