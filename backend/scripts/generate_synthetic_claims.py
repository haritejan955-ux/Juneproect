"""Generates synthetic historical claim decisions and indexes them into the
`historical_decisions` hybrid (dense + sparse) store — one of the three
required RAG sources. See docs/vector-db-architecture.md.

Incremental: a claim already present in the index (by `claim_id`) is
skipped, so re-running this script after adding a new synthetic claim to
`_SYNTHETIC_CLAIMS` only embeds and indexes the new one.

Usage: python -m scripts.generate_synthetic_claims
"""

import json
from pathlib import Path

from app.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.memory.database import create_db_engine, init_db, make_session_factory
from app.memory.embedding_cache_store import SqlEmbeddingCacheStore
from app.memory.vector_doc_store import SqlVectorDocStore
from app.vectorstore.embedding_cache import CachedEmbeddings
from app.vectorstore.embeddings import get_embeddings
from app.vectorstore.hybrid_store import HybridVectorStore

logger = get_logger(__name__)

INDEX_NAME = "historical_decisions"

_SYNTHETIC_CLAIMS: list[dict] = [
    {
        "claim_id": "synthetic-0001",
        "decision": "approved",
        "summary": (
            "Outpatient physical therapy following a workplace injury was approved in full; "
            "CPT 97110 matched diagnosis M54.5 and fell within the annual visit limit."
        ),
    },
    {
        "claim_id": "synthetic-0002",
        "decision": "partial_approved",
        "summary": (
            "An emergency room visit was approved, but a duplicate lab charge (CPT 80053 "
            "billed twice for the same date of service) was denied as duplicate billing."
        ),
    },
    {
        "claim_id": "synthetic-0003",
        "decision": "denied",
        "summary": (
            "A cosmetic procedure (CPT 15823) was denied as excluded under the policy's "
            "cosmetic-surgery exclusion clause; no ACA essential-benefit category applied."
        ),
    },
    {
        "claim_id": "synthetic-0004",
        "decision": "denied",
        "summary": (
            "A claim was denied for a date-of-service conflict: the procedure date fell 62 "
            "days after the policy's coverage end date."
        ),
    },
    {
        "claim_id": "synthetic-0005",
        "decision": "partial_approved",
        "summary": (
            "Upcoding was identified where CPT 99215 (high-complexity visit) was billed against "
            "a diagnosis inconsistent with that level of service; the claim was re-priced to "
            "CPT 99213 and approved at the lower level."
        ),
    },
]


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    output_dir = Path(settings.synthetic_claims_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    engine = create_db_engine(settings)
    init_db(engine)
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

    already_indexed_claim_ids = {
        metadata.get("claim_id")
        for _vector_id, _text, metadata in doc_store.get_all(INDEX_NAME)
        if metadata.get("claim_id")
    }

    new_texts: list[str] = []
    new_metadatas: list[dict] = []

    for record in _SYNTHETIC_CLAIMS:
        output_path = output_dir / f"{record['claim_id']}.json"
        output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

        if record["claim_id"] in already_indexed_claim_ids:
            logger.info(f"Skipping already-indexed {record['claim_id']}")
            continue

        new_texts.append(record["summary"])
        new_metadatas.append(
            {
                "doc_title": f"Historical decision {record['claim_id']}",
                "section": record["decision"],
                "claim_id": record["claim_id"],
            }
        )

    if new_texts:
        store.add_texts(new_texts, new_metadatas)
        store.save(settings.vector_index_dir)

    logger.info(
        f"Indexed {len(new_texts)} new synthetic claims "
        f"(skipped {len(_SYNTHETIC_CLAIMS) - len(new_texts)} already indexed)."
    )


if __name__ == "__main__":
    main()
