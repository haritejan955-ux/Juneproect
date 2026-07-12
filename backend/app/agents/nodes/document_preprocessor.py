"""[1] Document Preprocessor — LLM-free, deterministic.

Parses uploaded claim documents, chunks by clause/section (never fixed
token windows), preserves CPT/ICD-10 codes, and flags PII before any LLM
call happens anywhere downstream. See docs/agent-architecture.md section 2.
"""

from collections.abc import Awaitable, Callable

import fitz  # PyMuPDF

from app.core.audit import audit_update
from app.core.exceptions import InvalidUploadError
from app.core.logging import get_logger
from app.security.pii_redactor import flag_pii
from app.state.graph_state import DocumentChunk, GraphState
from app.vectorstore.chunking import chunk_by_clause

AGENT_NAME = "document_preprocessor"

logger = get_logger(__name__)


def _extract_text(storage_path: str) -> str:
    with fitz.open(storage_path) as doc:
        return "\n\n".join(page.get_text() for page in doc)


def build_document_preprocessor_node() -> Callable[[GraphState], Awaitable[dict]]:
    async def document_preprocessor(state: GraphState) -> dict:
        claim_id = state["claim_id"]
        claim_document = state.get("claim_document", [])
        logger.info(
            f"{AGENT_NAME}.started",
            extra={"claim_id": claim_id, "document_count": len(claim_document)},
        )

        all_chunks: list[DocumentChunk] = []
        doc_types_seen: set[str] = set()
        failed_files: list[str] = []

        for raw_doc in claim_document:
            # Each file is untrusted, externally-supplied input (a claimant's upload) — a
            # corrupt or malformed PDF from one file must not crash the whole node when other
            # files in the same submission are fine. It's tracked and surfaced below instead.
            try:
                text = _extract_text(raw_doc["storage_path"])
            except Exception as exc:
                logger.warning(
                    f"{AGENT_NAME}.file_parse_failed",
                    extra={
                        # `filename` collides with logging.LogRecord's own reserved attribute
                        # (the source .py file); use `upload_filename` for the claim's file.
                        "claim_id": claim_id,
                        "upload_filename": raw_doc["filename"],
                        "error": str(exc),
                    },
                    exc_info=True,
                )
                failed_files.append(raw_doc["filename"])
                continue

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

        if claim_document and not all_chunks:
            logger.error(
                f"{AGENT_NAME}.no_usable_content",
                extra={"claim_id": claim_id, "failed_files": failed_files},
            )
            raise InvalidUploadError(
                "None of the uploaded documents could be parsed into usable content.",
                claim_id=claim_id,
                failed_files=failed_files,
            )

        # `pii_flags` (per-chunk detail: which chunk, which field label) is only ever consumed
        # here, for the audit trail — GraphState only needs the boolean `pii_detected` for any
        # future node/route to branch on. See PIIFlag's docstring in security/pii_redactor.py.
        pii_flags = flag_pii(all_chunks)

        logger.info(
            f"{AGENT_NAME}.completed",
            extra={
                "claim_id": claim_id,
                "chunk_count": len(all_chunks),
                "failed_file_count": len(failed_files),
                "pii_detected": bool(pii_flags),
            },
        )

        return {
            "chunks": all_chunks,
            "document_metadata": {
                "document_count": len(claim_document),
                "doc_types": sorted(doc_types_seen),
                "chunk_count": len(all_chunks),
                "failed_files": failed_files,
            },
            "pii_detected": bool(pii_flags),
            **audit_update(
                AGENT_NAME,
                "parsed_and_chunked_documents",
                {
                    "chunk_count": len(all_chunks),
                    "pii_flag_count": len(pii_flags),
                    "pii_flags": pii_flags,
                    "failed_files": failed_files,
                },
            ),
        }

    return document_preprocessor
