"""SQLAlchemy table definitions — the durable, queryable record.

Distinct from `app.state.graph_state.GraphState` (in-flight LangGraph state)
and `app.schemas.*` (API DTOs) on purpose; see docs/architecture.md section
2 for why these three layers are kept separate. See
docs/database-architecture.md for the ERD and per-table rationale.
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid() -> str:
    return str(uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Claimant(Base):
    __tablename__ = "claimants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    external_ref: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claimant_id: Mapped[str] = mapped_column(ForeignKey("claimants.id"), index=True)
    query: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="processing")
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    intent_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ClaimDocument(Base):
    __tablename__ = "claim_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    doc_type: Mapped[str] = mapped_column(String(64))
    storage_path: Mapped[str] = mapped_column(String(512))
    pii_flagged: Mapped[bool] = mapped_column(Boolean, default=False)


class ClaimDecision(Base):
    __tablename__ = "claim_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id"), unique=True, index=True)
    decision: Mapped[str] = mapped_column(String(32))
    confidence_score: Mapped[float] = mapped_column(Float)
    low_confidence_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    attorney_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    justification: Mapped[str] = mapped_column(Text)
    disclaimer: Mapped[str] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CoverageLineItemRecord(Base):
    __tablename__ = "coverage_line_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_decision_id: Mapped[str] = mapped_column(ForeignKey("claim_decisions.id"), index=True)
    cpt_code: Mapped[str] = mapped_column(String(16))
    diagnosis_code: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    cited_clause: Mapped[str] = mapped_column(Text)
    amount_billed: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount_covered: Mapped[float | None] = mapped_column(Float, nullable=True)


class FraudSignalRecord(Base):
    __tablename__ = "fraud_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_decision_id: Mapped[str] = mapped_column(ForeignKey("claim_decisions.id"), index=True)
    signal_type: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(16))
    evidence: Mapped[str] = mapped_column(Text)


class CitationRecord(Base):
    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_decision_id: Mapped[str] = mapped_column(ForeignKey("claim_decisions.id"), index=True)
    source_doc: Mapped[str] = mapped_column(String(255))
    section: Mapped[str | None] = mapped_column(String(128), nullable=True)
    excerpt: Mapped[str] = mapped_column(Text)


class AuditLogEntryRecord(Base):
    __tablename__ = "audit_log_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(128))
    details_json: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="open")
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class DisputeMessageRecord(Base):
    __tablename__ = "dispute_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dispute_id: Mapped[str] = mapped_column(ForeignKey("disputes.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class VectorDocumentRecord(Base):
    """Text + metadata for one FAISS vector — see docs/vector-db-architecture.md."""

    __tablename__ = "vector_documents"

    index_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    vector_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text)


class EmbeddingCacheRecord(Base):
    """A previously-computed embedding, keyed by a hash of (model_name, text) so it survives
    process restarts and is shared across ingestion runs, retrieval queries, and re-indexing —
    see vectorstore/embedding_cache.py. Keyed by hash rather than the raw text itself: text can
    be arbitrarily long (a whole chunk), and SQLite primary keys are more efficient short and
    fixed-width."""

    __tablename__ = "embedding_cache"

    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    model_name: Mapped[str] = mapped_column(String(128))
    embedding_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
