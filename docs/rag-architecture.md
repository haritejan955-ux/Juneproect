# RAG / Vector Store Architecture

## Corpus

`backend/app/data/interaction_corpus/*.md` — 10 curated drug-interaction monographs, each a
markdown file with a JSON frontmatter block (`drug_pair`, `severity`, `title`) followed by a
clinical description and management guidance. Parsed by `backend/app/rag/loader.py`.

This is a small, hand-curated corpus (not a scrape of a real interaction database like
Micromedex or Lexicomp, which are proprietary) — it's representative and covers the
project's test scenarios, not exhaustive. See `docs/design-decisions.md` for why.

## Embedding cache (incremental indexing)

`backend/app/rag/cache.py::EmbeddingCache` persists a `content_hash → embedding vector` map
as JSON. Rebuilding the index (`scripts/build_interaction_index.py`, safe to re-run) only
calls the embeddings API for monographs whose content hash isn't already cached — editing one
monograph and re-running the build re-embeds exactly that one document, not all ten.
`backend/tests/unit/test_embedding_cache.py` proves this: re-running `get_or_embed` with the
same texts makes zero additional embedding calls.

## Retrieval

`backend/app/rag/store.py::InteractionRetriever` wraps a FAISS index (`langchain_community.vectorstores.FAISS`,
built via `FAISS.from_embeddings` so the cache's precomputed vectors are reused directly
rather than re-embedded through `from_documents`). Each vector's metadata carries `doc_id`,
`title`, `severity`, and `drug_pair`.

The Interaction Retriever node (`backend/app/agents/nodes/interaction_retriever.py`) queries
`"{drug_a} and {drug_b} drug interaction"` for every unique pair of recognized medications, then
verifies each of the top-k hits' `drug_pair` metadata actually contains both drug names before
accepting it as a finding. This hybrid of semantic search + metadata verification means a
near-miss embedding match can never fabricate a citation for a pair the corpus doesn't
actually cover — the citation is only ever attached when the retrieved monograph's own
`drug_pair` field names both drugs.

## Why FAISS over a managed vector DB

At ten documents, a managed vector database (Pinecone, Weaviate, etc.) would be pure
operational overhead. FAISS persisted to local disk (`app/data/indices/interactions/`) is
sufficient for this project's scale and keeps the whole RAG layer runnable with zero external
services beyond the embeddings API itself.
