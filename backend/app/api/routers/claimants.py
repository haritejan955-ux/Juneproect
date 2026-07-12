from fastapi import APIRouter, Depends

from app.api.auth import require_api_key
from app.api.dependencies import get_claim_repository
from app.memory.repository import ClaimRepository
from app.schemas.claimant import ClaimantHistoryResponse, ClaimHistoryEntry

router = APIRouter(
    prefix="/api/v1/claimants", tags=["claimants"], dependencies=[Depends(require_api_key)]
)


@router.get("/{claimant_id}/history", response_model=ClaimantHistoryResponse)
async def get_claimant_history(
    claimant_id: str, repository: ClaimRepository = Depends(get_claim_repository)
) -> ClaimantHistoryResponse:
    """Long-term memory read path — an exact-match SQL lookup by claimant
    ID, not a vector search. See docs/memory-architecture.md section 2."""
    claims = repository.get_claimant_history(claimant_id)
    return ClaimantHistoryResponse(
        claimant_id=claimant_id,
        claims=[
            ClaimHistoryEntry(
                claim_id=claim.id,
                query=claim.query,
                status=claim.status,
                submitted_at=claim.submitted_at,
            )
            for claim in claims
        ],
    )
