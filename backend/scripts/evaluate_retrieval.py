"""Retrieval evaluation harness for the `policy_corpus` index.

Not a full RAGAS-style framework — there's no labeled, human-curated
retrieval dataset for this corpus (six representative policy documents),
so a heavyweight evaluation framework would be measuring against a target
that doesn't exist yet. This is the right-sized alternative: a fixed set
of realistic queries, each with a known expected source document, scored
as a recall@k proxy (did the expected document appear in the top k
results), run against both hybrid (dense+sparse) and dense-only retrieval
so the hybrid retrieval feature's actual effect is visible, not asserted.

Extend `EVAL_QUERIES` as the corpus grows; the harness itself doesn't
change.

Usage: python -m scripts.evaluate_retrieval
"""

import time
from collections.abc import Callable
from dataclasses import dataclass

from app.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.memory.database import create_db_engine, make_session_factory
from app.memory.embedding_cache_store import SqlEmbeddingCacheStore
from app.memory.vector_doc_store import SqlVectorDocStore
from app.vectorstore.base import ScoredChunk
from app.vectorstore.embedding_cache import CachedEmbeddings
from app.vectorstore.embeddings import get_embeddings
from app.vectorstore.hybrid_store import HybridVectorStore

logger = get_logger(__name__)

INDEX_NAME = "policy_corpus"


@dataclass(frozen=True)
class EvalQuery:
    query: str
    expected_doc_title_substring: str
    description: str


EVAL_QUERIES: list[EvalQuery] = [
    EvalQuery(
        query="What are the ACA essential health benefit categories?",
        expected_doc_title_substring="aca",
        description="semantic match — no shared exact terms with the doc title",
    ),
    EvalQuery(
        query="How many days does Medicare Part A cover in a skilled nursing facility?",
        expected_doc_title_substring="cms_medicare",
        description="semantic + partial term overlap (Medicare)",
    ),
    EvalQuery(
        query="What is the deadline in California to acknowledge an insurance claim?",
        expected_doc_title_substring="ca_fair_claims",
        description="semantic + partial term overlap (California, claim)",
    ),
    EvalQuery(
        query="10 CCR 2695.7 acceptance or denial deadline",
        expected_doc_title_substring="ca_fair_claims",
        description="exact statute citation — favors sparse/BM25 retrieval",
    ),
    EvalQuery(
        query="What must a NAIC-compliant denial letter include?",
        expected_doc_title_substring="naic",
        description="semantic + partial term overlap (NAIC, denial)",
    ),
    EvalQuery(
        query="Proof of Loss deadline for a flood insurance claim",
        expected_doc_title_substring="fema",
        description="semantic + partial term overlap (flood, Proof of Loss)",
    ),
    EvalQuery(
        query="How does a federal employee health plan coordinate with Medicare?",
        expected_doc_title_substring="fehb",
        description="semantic match — 'FEHB' never appears in the query itself",
    ),
]


@dataclass
class QueryResult:
    query: str
    hit: bool
    top_doc_titles: list[str]
    top_score: float
    low_confidence: bool
    latency_ms: float


def evaluate_query(
    search_fn: Callable[[str, int, float, str], list[ScoredChunk]],
    case: EvalQuery,
    k: int,
    threshold: float,
) -> QueryResult:
    """Pure function — takes a bound search callable rather than a store, so it can be
    unit-tested against a fake without any real embeddings/index."""
    start = time.perf_counter()
    results = search_fn(case.query, k, threshold, "policy_corpus")
    latency_ms = (time.perf_counter() - start) * 1000

    top_doc_titles = [str(r["metadata"].get("doc_title", "")) for r in results]
    expected = case.expected_doc_title_substring.lower()
    hit = any(expected in title.lower() for title in top_doc_titles)

    return QueryResult(
        query=case.query,
        hit=hit,
        top_doc_titles=top_doc_titles,
        top_score=results[0]["score"] if results else 0.0,
        low_confidence=results[0]["low_confidence"] if results else True,
        latency_ms=latency_ms,
    )


def _print_report(label: str, results: list[QueryResult]) -> None:
    hits = sum(1 for r in results if r.hit)
    avg_latency = sum(r.latency_ms for r in results) / len(results) if results else 0.0

    print(f"\n=== {label} — recall@k: {hits}/{len(results)} ===")
    for result in results:
        status = "HIT " if result.hit else "MISS"
        print(
            f"  [{status}] {result.latency_ms:6.1f}ms  score={result.top_score:.3f}  "
            f"low_confidence={result.low_confidence}  \"{result.query[:60]}\""
        )
        print(f"           top doc_titles: {result.top_doc_titles}")
    print(f"  avg latency: {avg_latency:.1f}ms")


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    engine = create_db_engine(settings)
    session_factory = make_session_factory(engine)

    raw_embeddings = get_embeddings(settings)
    embeddings = CachedEmbeddings(
        inner=raw_embeddings,
        store=SqlEmbeddingCacheStore(session_factory),
        model_name=settings.openai_embedding_model,
    )
    doc_store = SqlVectorDocStore(session_factory)
    store = HybridVectorStore.load_or_create(
        settings.vector_index_dir, INDEX_NAME, embeddings, doc_store
    )

    if not doc_store.get_all(INDEX_NAME):
        logger.error(
            f"'{INDEX_NAME}' index is empty. Run `python -m scripts.build_policy_index` first."
        )
        return

    top_k = settings.rag_top_k
    threshold = settings.rag_similarity_threshold

    hybrid_results = [
        evaluate_query(store.search, case, k=top_k, threshold=threshold) for case in EVAL_QUERIES
    ]
    dense_only_results = [
        evaluate_query(store.search_dense_only, case, k=top_k, threshold=threshold)
        for case in EVAL_QUERIES
    ]

    _print_report("Hybrid (dense + sparse, RRF-fused)", hybrid_results)
    _print_report("Dense-only (baseline)", dense_only_results)

    hybrid_hits = sum(1 for r in hybrid_results if r.hit)
    dense_hits = sum(1 for r in dense_only_results if r.hit)
    print(
        f"\nSummary: hybrid recall@{settings.rag_top_k} = {hybrid_hits}/{len(EVAL_QUERIES)}, "
        f"dense-only recall@{settings.rag_top_k} = {dense_hits}/{len(EVAL_QUERIES)}"
    )


if __name__ == "__main__":
    main()
