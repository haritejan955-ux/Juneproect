"""[1] Document Preprocessor — LLM-free, deterministic.

Parses uploaded claim documents, chunks by clause/section (never fixed
token windows), preserves CPT/ICD-10 codes, and flags PII before any LLM
call happens anywhere downstream. See docs/agent-architecture.md section 2.
"""

from collections.abc import Awaitable, Callable

import fitz  # PyMuPDF

from app.core.audit import audit_update
from app.security.pii_redactor import flag_pii
from app.state.graph_state import DocumentChunk, GraphState
from app.vectorstore.chunking import chunk_by_clause

AGENT_NAME = "document_preprocessor"


def _extract_text(storage_path: str) -> str:
    with fitz.open(storage_path) as doc:
        return "\n\n".join(page.get_text() for page in doc)


def build_document_preprocessor_node() -> Callable[[GraphState], Awaitable[dict]]:
    async def document_preprocessor(state: GraphState) -> dict:
        raw_documents = state.get("raw_documents", [])
        all_chunks: list[DocumentChunk] = []
        doc_types_seen: set[str] = set()

        for raw_doc in raw_documents:
            text = _extract_text(raw_doc["storage_path"])
            doc_type = raw_doc["doc_type"]
            doc_types_seen.add(doc_type)
            for chunk in chunk_by_clause(text, doc_type=doc_type):
                all_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk.chunk_id,
                        text=chunk.text,
                        section=chunk.section,
                        doc_type=doc_type,
                        preserved_codes=chunk.preserved_codes,
                    )
                )

        pii_flags = flag_pii(all_chunks)

        return {
            "document_chunks": all_chunks,
            "document_metadata": {
                "document_count": len(raw_documents),
                "doc_types": sorted(doc_types_seen),
                "chunk_count": len(all_chunks),
            },
            "pii_flags": pii_flags,
            **audit_update(
                AGENT_NAME,
                "parsed_and_chunked_documents",
                {"chunk_count": len(all_chunks), "pii_flag_count": len(pii_flags)},
            ),
        }

    return document_preprocessor
