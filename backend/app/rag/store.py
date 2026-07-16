from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

from app.rag.cache import EmbeddingCache
from app.rag.loader import InteractionDoc, load_interaction_corpus


class InteractionRetriever:
    """FAISS-backed similarity search over the drug-interaction monograph corpus."""

    def __init__(self, vector_store: FAISS, docs_by_id: dict[str, InteractionDoc]):
        self._vector_store = vector_store
        self._docs_by_id = docs_by_id

    @classmethod
    def build(cls, corpus_dir: Path, index_dir: Path, embeddings: Embeddings) -> "InteractionRetriever":
        docs = load_interaction_corpus(corpus_dir)
        cache = EmbeddingCache(index_dir / "embedding_cache.json")
        vectors = cache.get_or_embed([d.text for d in docs], embeddings)

        text_embeddings = list(zip((d.text for d in docs), vectors, strict=True))
        metadatas = [
            {
                "doc_id": d.doc_id,
                "title": d.title,
                "severity": d.severity,
                "drug_pair": d.drug_pair,
                "source_path": d.source_path,
            }
            for d in docs
        ]
        vector_store = FAISS.from_embeddings(text_embeddings, embeddings, metadatas=metadatas)
        index_dir.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(index_dir))
        return cls(vector_store, {d.doc_id: d for d in docs})

    @classmethod
    def load(cls, corpus_dir: Path, index_dir: Path, embeddings: Embeddings) -> "InteractionRetriever":
        vector_store = FAISS.load_local(
            str(index_dir), embeddings, allow_dangerous_deserialization=True
        )
        docs = load_interaction_corpus(corpus_dir)
        return cls(vector_store, {d.doc_id: d for d in docs})

    def search(self, query: str, k: int = 3) -> list[dict]:
        results = self._vector_store.similarity_search_with_score(query, k=k)
        return [
            {
                "doc_id": doc.metadata["doc_id"],
                "title": doc.metadata["title"],
                "severity": doc.metadata["severity"],
                "drug_pair": doc.metadata["drug_pair"],
                "text": doc.page_content,
                "score": float(score),
            }
            for doc, score in results
        ]
