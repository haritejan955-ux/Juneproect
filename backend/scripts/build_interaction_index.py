"""Build (or incrementally update) the FAISS index over the drug-interaction corpus.

Safe to re-run: unchanged monographs are served from the embedding cache and never
re-embedded.
"""

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings
from app.rag.store import InteractionRetriever


def main() -> None:
    settings = get_settings()
    embeddings = get_embeddings()
    InteractionRetriever.build(
        settings.interaction_corpus_dir, settings.interaction_index_dir, embeddings
    )
    print(f"Built interaction index at {settings.interaction_index_dir}")


if __name__ == "__main__":
    main()
