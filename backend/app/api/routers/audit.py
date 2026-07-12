import json

from fastapi import APIRouter, Depends

from app.api.auth import require_api_key
from app.api.dependencies import get_claim_repository
from app.memory.repository import ClaimRepository
from app.schemas.audit import AuditLogEntryResponse, AuditTrailResponse

router = APIRouter(
    prefix="/api/v1/claims", tags=["audit"], dependencies=[Depends(require_api_key)]
)


@router.get("/{claim_id}/audit", response_model=AuditTrailResponse)
async def get_audit_trail(
    claim_id: str, repository: ClaimRepository = Depends(get_claim_repository)
) -> AuditTrailResponse:
    entries = repository.get_audit_trail(claim_id)
    return AuditTrailResponse(
        claim_id=claim_id,
        entries=[
            AuditLogEntryResponse(
                agent=entry.agent_name,
                action=entry.action,
                details=json.loads(entry.details_json),
                timestamp=entry.timestamp,
            )
            for entry in entries
        ],
    )
