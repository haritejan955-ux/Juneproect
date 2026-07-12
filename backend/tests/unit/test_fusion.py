from app.vectorstore.fusion import reciprocal_rank_fusion


def test_single_ranking_preserves_order():
    ranking = [(10, 0.9), (20, 0.5), (30, 0.1)]
    fused = reciprocal_rank_fusion(ranking)
    assert [item_id for item_id, _ in fused] == [10, 20, 30]


def test_item_in_both_rankings_outranks_item_in_only_one():
    dense = [(1, 0.9), (2, 0.8), (3, 0.7)]
    sparse = [(3, 5.0), (4, 4.0)]
    fused = reciprocal_rank_fusion(dense, sparse)
    fused_ids = [item_id for item_id, _ in fused]
    # item 3 appears in both rankings (dense rank 2, sparse rank 0) — its fused score is the
    # sum of both contributions, so it should outrank item 1 (dense rank 0, no sparse presence).
    assert fused_ids.index(3) < fused_ids.index(1)


def test_empty_rankings_produce_empty_fusion():
    assert reciprocal_rank_fusion([], []) == []


def test_disjoint_rankings_are_merged():
    dense = [(1, 0.9)]
    sparse = [(2, 5.0)]
    fused = reciprocal_rank_fusion(dense, sparse)
    assert {item_id for item_id, _ in fused} == {1, 2}


def test_smaller_k_makes_top_rank_dominate_more():
    dense = [(1, 0.9), (2, 0.8)]
    fused_small_k = dict(reciprocal_rank_fusion(dense, k=1))
    fused_large_k = dict(reciprocal_rank_fusion(dense, k=1000))
    # With a small k, the gap between rank 0 and rank 1 is proportionally larger.
    ratio_small_k = fused_small_k[1] / fused_small_k[2]
    ratio_large_k = fused_large_k[1] / fused_large_k[2]
    assert ratio_small_k > ratio_large_k
