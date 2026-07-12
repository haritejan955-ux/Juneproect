from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ClaimStatus = Literal["processing", "completed", "blocked", "failed"]


class ClaimSubmitResponse(BaseModel):
    claim_id: str
    status: ClaimStatus = "processing"


class ClaimStatusResponse(BaseModel):
    claim_id: str
    claimant_id: str
    status: ClaimStatus
    query: str
    intent: str | None = None
    intent_confidence: float | None = None
    submitted_at: datetime


class ClaimDocumentSummary(BaseModel):
    filename: str
    doc_type: str
    pii_flagged: bool = Field(
        default=False, description="True if the Document Preprocessor flagged PII in this file"
    )
