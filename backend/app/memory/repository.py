"""Durable, queryable business records — the long-term memory tier.

Distinct from the LangGraph checkpointer (run-scoped, see checkpointer.py):
this repository is what `GET /claims/{id}/decision`, the Audit Trail
screen, and claimant history lookups actually read from, and it is what
survives a server restart. See docs/memory-architecture.md.
"""

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ClaimantNotFoundError, ClaimNotFoundError, DisputeNotFoundError
from app.memory.models import (
    AuditLogEntryRecord,
    CitationRecord,
    Claim,
    Claimant,
    ClaimDecision,
    ClaimDocument,
    CoverageLineItemRecord,
    Dispute,
    DisputeMessageRecord,
    FraudSignalRecord,
)
from app.state.graph_state import AuditLogEntry, FinalDecision


class ClaimRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    # --- Claimants ---

    def get_or_create_claimant(self, external_ref: str) -> Claimant:
        stmt = select(Claimant).where(Claimant.external_ref == external_ref)
        claimant = self._session.scalars(stmt).first()
        if claimant is not None:
            return claimant
        claimant = Claimant(external_ref=external_ref)
        self._session.add(claimant)
        self._session.commit()
        self._session.refresh(claimant)
        return claimant

    # --- Claims ---

    def create_claim(self, claim_id: str, claimant_id: str, query: str) -> Claim:
        claim = Claim(id=claim_id, claimant_id=claimant_id, query=query, status="processing")
        self._session.add(claim)
        self._session.commit()
        self._session.refresh(claim)
        return claim

    def get_claim(self, claim_id: str) -> Claim:
        claim = self._session.get(Claim, claim_id)
        if claim is None:
            raise ClaimNotFoundError(f"Claim {claim_id} not found", claim_id=claim_id)
        return claim

    def add_documents(
        self, claim_id: str, documents: list[dict], pii_flagged_filenames: set[str]
    ) -> None:
        for doc in documents:
            self._session.add(
                ClaimDocument(
                    claim_id=claim_id,
                    filename=doc["filename"],
                    doc_type=doc["doc_type"],
                    storage_path=doc["storage_path"],
                    pii_flagged=doc["filename"] in pii_flagged_filenames,
                )
            )
        self._session.commit()

    def update_claim_status(
        self,
        claim_id: str,
        status: str,
        intent: str | None = None,
        intent_confidence: float | None = None,
    ) -> None:
        claim = self.get_claim(claim_id)
        claim.status = status
        if intent is not None:
            claim.intent = intent
        if intent_confidence is not None:
            claim.intent_confidence = intent_confidence
        self._session.commit()

    # --- Decisions ---

    def save_decision(self, claim_id: str, final_decision: FinalDecision) -> ClaimDecision:
        decision = ClaimDecision(
            claim_id=claim_id,
            decision=final_decision["status"],
            confidence_score=final_decision["confidence_score"],
            low_confidence_flag=final_decision["low_confidence"],
            attorney_flag=final_decision["attorney_flag"],
            justification=final_decision["justification"],
            disclaimer=final_decision["disclaimer"],
            retry_count=final_decision["retry_count"],
        )
        self._session.add(decision)
        self._session.flush()

        for item in final_decision["coverage_map"]:
            self._session.add(
                CoverageLineItemRecord(claim_decision_id=decision.id, **item)
            )
        for signal in final_decision["fraud_signals"]:
            self._session.add(
                FraudSignalRecord(claim_decision_id=decision.id, **signal)
            )
        for citation in final_decision["citations"]:
            self._session.add(
                CitationRecord(claim_decision_id=decision.id, **citation)
            )

        self._session.commit()
        self._session.refresh(decision)
        return decision

    def get_decision(self, claim_id: str) -> ClaimDecision | None:
        stmt = select(ClaimDecision).where(ClaimDecision.claim_id == claim_id)
        return self._session.scalars(stmt).first()

    def get_coverage_line_items(self, claim_decision_id: str) -> list[CoverageLineItemRecord]:
        stmt = select(CoverageLineItemRecord).where(
            CoverageLineItemRecord.claim_decision_id == claim_decision_id
        )
        return list(self._session.scalars(stmt).all())

    def get_fraud_signals(self, claim_decision_id: str) -> list[FraudSignalRecord]:
        stmt = select(FraudSignalRecord).where(
            FraudSignalRecord.claim_decision_id == claim_decision_id
        )
        return list(self._session.scalars(stmt).all())

    def get_citations(self, claim_decision_id: str) -> list[CitationRecord]:
        stmt = select(CitationRecord).where(CitationRecord.claim_decision_id == claim_decision_id)
        return list(self._session.scalars(stmt).all())

    # --- Audit log (append-only, per docs/database-architecture.md) ---

    def append_audit_entries(self, claim_id: str, entries: list[AuditLogEntry]) -> None:
        for entry in entries:
            self._session.add(
                AuditLogEntryRecord(
                    claim_id=claim_id,
                    agent_name=entry["agent"],
                    action=entry["action"],
                    details_json=json.dumps(entry["details"]),
                    timestamp=datetime.fromisoformat(entry["timestamp"]),
                )
            )
        self._session.commit()

    def get_audit_trail(self, claim_id: str) -> list[AuditLogEntryRecord]:
        stmt = (
            select(AuditLogEntryRecord)
            .where(AuditLogEntryRecord.claim_id == claim_id)
            .order_by(AuditLogEntryRecord.timestamp.asc())
        )
        return list(self._session.scalars(stmt).all())

    # --- Claimant history (long-term memory read path) ---

    def get_claimant_history(self, external_ref: str) -> list[Claim]:
        claimant_stmt = select(Claimant).where(Claimant.external_ref == external_ref)
        claimant = self._session.scalars(claimant_stmt).first()
        if claimant is None:
            raise ClaimantNotFoundError(
                f"Claimant {external_ref} not found", claimant_id=external_ref
            )
        stmt = (
            select(Claim)
            .where(Claim.claimant_id == claimant.id)
            .order_by(Claim.submitted_at.desc())
        )
        return list(self._session.scalars(stmt).all())

    # --- Disputes (conversation memory tier) ---

    def get_or_create_dispute(self, claim_id: str) -> Dispute:
        stmt = select(Dispute).where(Dispute.claim_id == claim_id)
        dispute = self._session.scalars(stmt).first()
        if dispute is not None:
            return dispute
        dispute = Dispute(claim_id=claim_id, status="open")
        self._session.add(dispute)
        self._session.commit()
        self._session.refresh(dispute)
        return dispute

    def get_dispute(self, claim_id: str) -> Dispute:
        stmt = select(Dispute).where(Dispute.claim_id == claim_id)
        dispute = self._session.scalars(stmt).first()
        if dispute is None:
            raise DisputeNotFoundError(
                f"No dispute open for claim {claim_id}", claim_id=claim_id
            )
        return dispute

    def append_dispute_message(
        self, dispute_id: str, role: str, content: str
    ) -> DisputeMessageRecord:
        message = DisputeMessageRecord(
            dispute_id=dispute_id,
            role=role,
            content=content,
            timestamp=datetime.now(UTC),
        )
        self._session.add(message)
        self._session.commit()
        self._session.refresh(message)
        return message

    def get_dispute_messages(self, dispute_id: str) -> list[DisputeMessageRecord]:
        stmt = (
            select(DisputeMessageRecord)
            .where(DisputeMessageRecord.dispute_id == dispute_id)
            .order_by(DisputeMessageRecord.timestamp.asc())
        )
        return list(self._session.scalars(stmt).all())
