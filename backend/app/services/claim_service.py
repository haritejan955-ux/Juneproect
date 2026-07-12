"""Orchestrates claim submission and pipeline execution.

Routers never touch the graph, the repository, or the filesystem directly —
they call this service. See docs/api-architecture.md section 1 for why this
layer exists (mainly: a full 9-node LLM run can't happen inside a blocking
HTTP request handler).
"""

import contextlib
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session, sessionmaker

from app.core.logging import get_logger
from app.memory.checkpointer import thread_config
from app.memory.repository import ClaimRepository
from app.services.streaming import StreamPublisher
from app.state.graph_state import GraphState, RawDocument

logger = get_logger(__name__)

_DOC_TYPE_HINTS = {
    "cms1500": "cms_1500",
    "cms-1500": "cms_1500",
    "eob": "eob_statement",
    "denial": "denial_letter",
    "accident": "accident_report",
}


def _infer_doc_type(filename: str) -> str:
    lowered = filename.lower()
    for hint, doc_type in _DOC_TYPE_HINTS.items():
        if hint in lowered:
            return doc_type
    return "unspecified"


class ClaimService:
    def __init__(
        self,
        graph: CompiledStateGraph,
        session_factory: sessionmaker[Session],
        upload_storage_dir: str,
        stream_publisher: StreamPublisher,
    ) -> None:
        self._graph = graph
        self._session_factory = session_factory
        self._upload_storage_dir = Path(upload_storage_dir)
        self._stream_publisher = stream_publisher

    @contextlib.contextmanager
    def _repository(self) -> Iterator[ClaimRepository]:
        with self._session_factory() as session:
            yield ClaimRepository(session)

    async def submit_claim(
        self, claimant_external_ref: str, query: str, files: list[UploadFile]
    ) -> tuple[str, list[RawDocument]]:
        claim_id = str(uuid.uuid4())
        self._upload_storage_dir.mkdir(parents=True, exist_ok=True)

        raw_documents: list[RawDocument] = []
        for upload in files:
            filename = upload.filename or f"document_{uuid.uuid4().hex}.pdf"
            destination = self._upload_storage_dir / f"{claim_id}_{filename}"
            destination.write_bytes(await upload.read())
            raw_documents.append(
                RawDocument(
                    filename=filename,
                    storage_path=str(destination),
                    doc_type=_infer_doc_type(filename),
                    content_type=upload.content_type or "application/pdf",
                )
            )

        with self._repository() as repository:
            claimant = repository.get_or_create_claimant(claimant_external_ref)
            repository.create_claim(claim_id, claimant.id, query)
            repository.add_documents(
                claim_id,
                [
                    {
                        "filename": doc["filename"],
                        "doc_type": doc["doc_type"],
                        "storage_path": doc["storage_path"],
                    }
                    for doc in raw_documents
                ],
                pii_flagged_filenames=set(),
            )

        return claim_id, raw_documents

    async def run_claim_pipeline(
        self,
        claim_id: str,
        claimant_external_ref: str,
        query: str,
        raw_documents: list[RawDocument],
    ) -> None:
        initial_state: GraphState = {
            "claim_id": claim_id,
            "claimant_id": claimant_external_ref,
            "query": query,
            "raw_documents": raw_documents,
            "retry_count": 0,
            "audit_log": [],
        }

        try:
            async for event in self._graph.astream(
                initial_state, config=thread_config(claim_id), stream_mode="updates"
            ):
                for node_name, node_output in event.items():
                    await self._stream_publisher.publish(
                        claim_id,
                        {
                            "agent": node_name,
                            "status": "completed",
                            "timestamp": datetime.now(UTC).isoformat(),
                        },
                    )
                    if node_output and node_output.get("audit_log"):
                        with self._repository() as repository:
                            repository.append_audit_entries(claim_id, node_output["audit_log"])

            snapshot = await self._graph.aget_state(thread_config(claim_id))
            final_decision = snapshot.values.get("final_decision")

            with self._repository() as repository:
                if final_decision:
                    repository.save_decision(claim_id, final_decision)
                    # `claims.status` is the pipeline lifecycle state, distinct from
                    # the decision outcome (approved/partial_approved/denied) stored
                    # on ClaimDecision.decision — see docs/database-architecture.md.
                    lifecycle_status = (
                        "blocked" if final_decision["status"] == "blocked" else "completed"
                    )
                    repository.update_claim_status(
                        claim_id,
                        status=lifecycle_status,
                        intent=snapshot.values.get("intent"),
                        intent_confidence=snapshot.values.get("intent_confidence"),
                    )
                else:
                    repository.update_claim_status(claim_id, status="failed")

        except Exception:
            logger.exception("Claim pipeline failed for claim_id=%s", claim_id)
            with self._repository() as repository:
                repository.update_claim_status(claim_id, status="failed")
            raise
        finally:
            await self._stream_publisher.close(claim_id)
