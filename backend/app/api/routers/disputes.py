from fastapi import APIRouter, Depends

from app.api.dependencies import get_dispute_service
from app.schemas.dispute import (
    DisputeMessageRequest,
    DisputeMessageResponse,
    DisputeThreadResponse,
)
from app.services.dispute_service import DisputeService

router = APIRouter(prefix="/api/v1/claims", tags=["disputes"])


@router.post("/{claim_id}/dispute", response_model=DisputeMessageResponse)
async def post_dispute_message(
    claim_id: str,
    payload: DisputeMessageRequest,
    dispute_service: DisputeService = Depends(get_dispute_service),
) -> DisputeMessageResponse:
    reply = await dispute_service.post_message(claim_id, payload.message)
    return DisputeMessageResponse(**reply)


@router.get("/{claim_id}/dispute", response_model=DisputeThreadResponse)
async def get_dispute_thread(
    claim_id: str, dispute_service: DisputeService = Depends(get_dispute_service)
) -> DisputeThreadResponse:
    dispute_id, status, messages = dispute_service.get_thread(claim_id)
    return DisputeThreadResponse(
        dispute_id=dispute_id,
        claim_id=claim_id,
        status=status,  # type: ignore[arg-type]
        messages=[DisputeMessageResponse(**message) for message in messages],
    )
