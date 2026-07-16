from functools import lru_cache

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings
from app.rag.store import InteractionRetriever


@lru_cache
def get_interaction_retriever() -> InteractionRetriever:
    settings = get_settings()
    embeddings = get_embeddings()
    index_file = settings.interaction_index_dir / "index.faiss"
    if not index_file.exists():
        return InteractionRetriever.build(
            settings.interaction_corpus_dir, settings.interaction_index_dir, embeddings
        )
    return InteractionRetriever.load(
        settings.interaction_corpus_dir, settings.interaction_index_dir, embeddings
    )
