"""Builds the `policy_corpus` FAISS index from data/policy_corpus/*.md.

Idempotent: re-running against unchanged source files reproduces the same
index (given a deterministic embedding model). See
docs/vector-db-architecture.md section 3.

Usage: python -m scripts.build_policy_index
"""

from pathlib import Path

from app.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.memory.database import create_db_engine, init_db, make_session_factory
from app.memory.vector_doc_store import SqlVectorDocStore
from app.vectorstore.chunking import chunk_by_clause
from app.vectorstore.embeddings import get_embeddings
from app.vectorstore.faiss_store import FaissVectorStore

logger = get_logger(__name__)


def _doc_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return path.stem


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    corpus_dir = Path(settings.policy_corpus_dir)
    corpus_files = sorted(corpus_dir.glob("*.md"))
    if not corpus_files:
        logger.warning("No policy corpus files found in %s; index will be empty.", corpus_dir)

    engine = create_db_engine(settings)
    init_db(engine)
    session_factory = make_session_factory(engine)

    embeddings = get_embeddings(settings)
    doc_store = SqlVectorDocStore(session_factory)
    store = FaissVectorStore.load_or_create(
        settings.vector_index_dir, "policy_corpus", embeddings, doc_store
    )

    for path in corpus_files:
        text = path.read_text(encoding="utf-8")
        title = _doc_title(path)
        chunks = chunk_by_clause(text, doc_type="policy")
        if not chunks:
            continue
        store.add_texts(
            texts=[chunk.text for chunk in chunks],
            metadatas=[
                {"doc_title": title, "section": chunk.section, "source_file": path.name}
                for chunk in chunks
            ],
        )
        logger.info("Indexed %d chunks from %s", len(chunks), path.name)

    store.save(settings.vector_index_dir)
    logger.info("Saved policy_corpus index to %s", settings.vector_index_dir)


if __name__ == "__main__":
    main()
