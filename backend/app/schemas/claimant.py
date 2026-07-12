from datetime import datetime

from pydantic import BaseModel


class ClaimHistoryEntry(BaseModel):
    claim_id: str
    query: str
    status: str
    """Claim lifecycle status (processing/completed/blocked/failed) — not the
    decision outcome, which lives under GET /claims/{id}/decision."""
    submitted_at: datetime


class ClaimantHistoryResponse(BaseModel):
    claimant_id: str
    claims: list[ClaimHistoryEntry]
