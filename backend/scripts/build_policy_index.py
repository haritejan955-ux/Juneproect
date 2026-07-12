"""Builds/updates the `policy_corpus` hybrid (dense + sparse) index from
data/policy_corpus/*.{md,txt,pdf}.

Incremental: each chunk's content hash is checked against what's already
indexed before embedding, so re-running this script after adding one new
document only embeds that document's chunks — every other file's chunks
are skipped, not re-embedded and re-added as duplicates. Combined with the
embedding cache (any chunk whose exact text was already embedded anywhere,
even under a different index, is served from cache), a re-run over an
unchanged corpus makes zero embeddings API calls.

Usage: python -m scripts.build_policy_index
"""

from pathlib import Path

from app.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.memory.database import create_db_engine, init_db, make_session_factory
from app.memory.embedding_cache_store import SqlEmbeddingCacheStore
from app.memory.vector_doc_store import SqlVectorDocStore
from app.vectorstore.chunking import chunk_by_clause
from app.vectorstore.document_loading import SUPPORTED_EXTENSIONS, content_hash, load_document_text
from app.vectorstore.embedding_cache import CachedEmbeddings
from app.vectorstore.embeddings import get_embeddings
from app.vectorstore.hybrid_store import HybridVectorStore

logger = get_logger(__name__)

INDEX_NAME = "policy_corpus"


def _doc_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return fallback


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    corpus_dir = Path(settings.policy_corpus_dir)
    corpus_files = sorted(
        path for path in corpus_dir.glob("*") if path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not corpus_files:
        logger.warning(f"No policy corpus files found in {corpus_dir}; index will be empty.")

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

    already_indexed_hashes = {
        metadata.get("content_hash")
        for _vector_id, _text, metadata in doc_store.get_all(INDEX_NAME)
        if metadata.get("content_hash")
    }

    new_texts: list[str] = []
    new_metadatas: list[dict] = []
    skipped = 0

    for path in corpus_files:
        text = load_document_text(path)
        title = _doc_title(text, fallback=path.stem)
        chunks = chunk_by_clause(text, doc_type="policy")

        for chunk in chunks:
            chunk_hash = content_hash(chunk.text)
            if chunk_hash in already_indexed_hashes:
                skipped += 1
                continue
            new_texts.append(chunk.text)
            new_metadatas.append(
                {
                    "doc_title": title,
                    "section": chunk.section,
                    "source_file": path.name,
                    "content_hash": chunk_hash,
                }
            )
            already_indexed_hashes.add(chunk_hash)

        logger.info(f"Processed {path.name}: {len(chunks)} chunks (source may already be indexed)")

    if new_texts:
        store.add_texts(new_texts, new_metadatas)
        store.save(settings.vector_index_dir)

    logger.info(
        f"Indexed {len(new_texts)} new chunks, skipped {skipped} already-indexed chunks, "
        f"from {len(corpus_files)} source files."
    )


if __name__ == "__main__":
    main()
