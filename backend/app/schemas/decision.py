from datetime import datetime
from typing import Literal

from pydantic import BaseModel

DecisionStatus = Literal["approved", "partial_approved", "denied", "blocked"]
Severity = Literal["low", "medium", "high"]


class CoverageLineItemResponse(BaseModel):
    cpt_code: str
    diagnosis_code: str
    status: Literal["approved", "denied"]
    cited_clause: str
    amount_billed: float | None = None
    amount_covered: float | None = None


class FraudSignalResponse(BaseModel):
    signal_type: Literal["duplicate_billing", "upcoding", "date_conflict", "unbundling"]
    severity: Severity
    evidence: str


class CitationResponse(BaseModel):
    source_doc: str
    section: str | None = None
    excerpt: str


class DecisionResponse(BaseModel):
    claim_id: str
    status: DecisionStatus
    confidence_score: float
    low_confidence: bool
    attorney_flag: bool
    justification: str
    coverage_map: list[CoverageLineItemResponse]
    fraud_signals: list[FraudSignalResponse]
    citations: list[CitationResponse]
    disclaimer: str
    retry_count: int
    created_at: datetime
