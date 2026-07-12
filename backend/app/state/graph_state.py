"""The shared LangGraph state contract.

Every agent node reads a subset of these fields and returns a partial update
containing only the fields it owns (see docs/agent-architecture.md for the
full ownership table). `audit_log` is the one field every node writes to; it
uses the `operator.add` reducer so LangGraph appends each node's new entries
instead of one node's write overwriting another's.
"""

import operator
from typing import Annotated, Literal, TypedDict

Intent = Literal["coverage_check", "denial_appeal", "fraud_check", "obligation_lookup"]
Decision = Literal["approved", "partial_approved", "denied"]
Severity = Literal["low", "medium", "high"]
FraudSignalType = Literal["duplicate_billing", "upcoding", "date_conflict", "unbundling"]
RetrievalSource = Literal["claim_document", "policy_corpus", "historical_decision"]
PIIType = Literal["SSN", "DOB", "EIN"]
LineItemStatus = Literal["approved", "denied"]


class AuditLogEntry(TypedDict):
    agent: str
    action: str
    details: dict
    timestamp: str


class RawDocument(TypedDict):
    filename: str
    storage_path: str
    doc_type: str
    content_type: str


class DocumentChunk(TypedDict):
    chunk_id: str
    text: str
    section: str | None
    doc_type: str
    preserved_codes: list[str]


class PIIFlag(TypedDict):
    chunk_id: str
    pii_type: PIIType
    field_label: str | None


class RetrievedChunk(TypedDict):
    text: str
    source: RetrievalSource
    score: float
    section: str | None
    doc_title: str | None
    low_confidence: bool


class SecurityFlags(TypedDict):
    injection_detected: bool
    heuristic_matched_patterns: list[str]
    llm_confidence: float
    llm_reasoning: str | None


class CoverageLineItem(TypedDict):
    cpt_code: str
    diagnosis_code: str
    status: LineItemStatus
    cited_clause: str
    amount_billed: float | None
    amount_covered: float | None


class FraudSignal(TypedDict):
    signal_type: FraudSignalType
    severity: Severity
    evidence: str


class Citation(TypedDict):
    source_doc: str
    section: str | None
    excerpt: str


class FinalDecision(TypedDict):
    claim_id: str
    status: Literal["approved", "partial_approved", "denied", "blocked"]
    confidence_score: float
    low_confidence: bool
    attorney_flag: bool
    justification: str
    coverage_map: list[CoverageLineItem]
    fraud_signals: list[FraudSignal]
    citations: list[Citation]
    disclaimer: str
    retry_count: int


class GraphState(TypedDict, total=False):
    # --- input ---
    claim_id: str
    claimant_id: str
    query: str
    raw_documents: list[RawDocument]

    # --- [1] Document Preprocessor ---
    document_chunks: list[DocumentChunk]
    document_metadata: dict
    pii_flags: list[PIIFlag]

    # --- [2] Intent Analyzer ---
    intent: Intent
    intent_confidence: float
    extracted_entities: dict

    # --- [3] RAG Retriever ---
    retrieved_chunks: list[RetrievedChunk]
    low_confidence_retrieval: bool

    # --- [4] Security Checker ---
    security_flags: SecurityFlags
    injection_detected: bool
    redacted_chunks: list[RetrievedChunk]

    # --- [5] Coverage Validator ---
    coverage_map: list[CoverageLineItem]
    coverage_citations: list[Citation]

    # --- [6] Fraud Detector ---
    fraud_signals: list[FraudSignal]
    attorney_flag: bool

    # --- [7] Answer Synthesizer ---
    draft_decision: Decision
    justification: str
    disclaimer: str

    # --- [8] Self-Critic ---
    critic_score: float
    critique: str
    retry_count: int
    low_confidence: bool

    # --- [9] Final Output ---
    final_decision: FinalDecision

    # --- shared, accumulating ---
    audit_log: Annotated[list[AuditLogEntry], operator.add]
