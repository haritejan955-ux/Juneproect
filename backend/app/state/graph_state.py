"""The shared LangGraph state contract.

Every agent node reads a subset of these fields and returns a partial update
containing only the fields it owns (see docs/agent-architecture.md for the
full ownership table). `audit_log` and `conversation_history` are the two
fields that accumulate rather than overwrite; both use the `operator.add`
reducer so LangGraph appends new entries instead of one write clobbering
another's.

Field-level detail that no downstream node actually consumes (the specific
regex patterns an injection matched, which exact chunk had a PII hit) is
deliberately kept OUT of this schema and pushed into `audit_log` entry
`details` instead — see `app.security.pii_redactor.PIIFlag` and
`app.security.injection_detector.SecurityFlags`, which are the return types
of the detection functions but are not themselves state fields. What lands
in `GraphState` is the small set of booleans/scores routing and the API
actually need: `pii_detected`, `security_flag`, `fraud_score`.
"""

import operator
from typing import Annotated, Literal, TypedDict

Intent = Literal["coverage_check", "denial_appeal", "fraud_check", "obligation_lookup"]
Decision = Literal["approved", "partial_approved", "denied"]
Severity = Literal["low", "medium", "high"]
FraudSignalType = Literal["duplicate_billing", "upcoding", "date_conflict", "unbundling"]
# "claim_document" here is a per-chunk *source tag* on a RetrievedChunk (this chunk came from
# the claimant's own upload) — unrelated to the GraphState.claim_document field below, which
# holds the raw uploaded files themselves. Same word, two different things; see each docstring.
RetrievalSource = Literal["claim_document", "policy_corpus", "historical_decision"]
LineItemStatus = Literal["approved", "denied"]
ConversationRole = Literal["claimant", "assistant"]


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


class RetrievedChunk(TypedDict):
    text: str
    source: RetrievalSource
    score: float
    section: str | None
    doc_title: str | None
    low_confidence: bool


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


class ConversationTurn(TypedDict):
    """One message in the claimant/assistant dispute thread. Written by the
    dispute flow (`app.services.dispute_service`) via `graph.aupdate_state`
    against the claim's existing checkpointed thread — never by a node
    inside the main 9-agent run, since disputes don't re-enter that graph
    (see docs/memory-architecture.md section 3)."""

    role: ConversationRole
    content: str
    timestamp: str


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
    claim_document: list[RawDocument]
    """The uploaded file(s) for this claim — CMS-1500, EOB, accident report, denial letter can
    all be part of one submission, hence a list despite the singular field name."""

    # --- [1] Document Preprocessor ---
    chunks: list[DocumentChunk]
    document_metadata: dict
    pii_detected: bool
    """True if any chunk matched a PII pattern near a recognized field label. The specific
    chunk/type/label detail is not carried in state — it's written to this node's audit_log
    entry instead, since no downstream node branches on which specific field was flagged."""

    # --- [2] Intent Analyzer ---
    intent: Intent
    intent_confidence: float
    extracted_entities: dict

    # --- [3] RAG Retriever ---
    retrieved_chunks: list[RetrievedChunk]
    low_confidence_retrieval: bool

    # --- [4] Security Checker ---
    security_flag: bool
    """The hybrid (heuristic OR LLM-classifier) hard-block signal that `route_after_security`
    reads. Per-layer detail (which regex matched, the LLM's confidence/reasoning) is written to
    this node's audit_log entry, not stored here — routing only ever needs the boolean."""
    redacted_chunks: list[RetrievedChunk]

    # --- [5] Coverage Validator ---
    coverage: list[CoverageLineItem]
    citations: list[Citation]

    # --- [6] Fraud Detector ---
    fraud_signals: list[FraudSignal]
    fraud_score: float
    """Aggregate 0.0-1.0 score derived from `fraud_signals` (highest signal severity mapped to a
    number; 0.0 if no signals fired) — a single sortable/thresholdable value for the API and
    frontend, distinct from the itemized `fraud_signals` list itself."""
    attorney_flag: bool

    # --- [7] Answer Synthesizer ---
    decision: Decision
    justification: str
    disclaimer: str

    # --- [8] Self-Critic ---
    confidence: float
    self_critique: str
    retry_count: int
    low_confidence: bool

    # --- [9] Final Output ---
    final_decision: FinalDecision

    # --- shared, accumulating ---
    audit_log: Annotated[list[AuditLogEntry], operator.add]
    conversation_history: Annotated[list[ConversationTurn], operator.add]
    """The dispute Q&A thread for this claim. Empty for the duration of the main 9-node run;
    appended to by the dispute flow via `graph.aupdate_state` against this claim's thread_id,
    after the claim already has a finalized decision — see docs/memory-architecture.md."""
