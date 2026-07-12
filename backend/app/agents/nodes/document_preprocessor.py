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
        claim_document = state.get("claim_document", [])
        all_chunks: list[DocumentChunk] = []
        doc_types_seen: set[str] = set()

        for raw_doc in claim_document:
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

        # `pii_flags` (per-chunk detail: which chunk, which field label) is only ever consumed
        # here, for the audit trail — GraphState only needs the boolean `pii_detected` for any
        # future node/route to branch on. See PIIFlag's docstring in security/pii_redactor.py.
        pii_flags = flag_pii(all_chunks)

        return {
            "chunks": all_chunks,
            "document_metadata": {
                "document_count": len(claim_document),
                "doc_types": sorted(doc_types_seen),
                "chunk_count": len(all_chunks),
            },
            "pii_detected": bool(pii_flags),
            **audit_update(
                AGENT_NAME,
                "parsed_and_chunked_documents",
                {
                    "chunk_count": len(all_chunks),
                    "pii_flag_count": len(pii_flags),
                    "pii_flags": pii_flags,
                },
            ),
        }

    return document_preprocessor
