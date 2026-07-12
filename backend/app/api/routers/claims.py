from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile

from app.api.dependencies import get_claim_repository, get_claim_service
from app.memory.repository import ClaimRepository
from app.schemas.claim import ClaimStatusResponse, ClaimSubmitResponse
from app.services.claim_service import ClaimService

router = APIRouter(prefix="/api/v1/claims", tags=["claims"])


@router.post("", response_model=ClaimSubmitResponse, status_code=202)
async def submit_claim(
    background_tasks: BackgroundTasks,
    claimant_id: str = Form(...),
    query: str = Form(...),
    files: list[UploadFile] = File(...),
    claim_service: ClaimService = Depends(get_claim_service),
) -> ClaimSubmitResponse:
    """Kicks off graph execution as a background task and returns
    immediately — see docs/api-architecture.md section 1 for why this
    cannot run synchronously in the request handler."""
    claim_id, raw_documents = await claim_service.submit_claim(claimant_id, query, files)
    background_tasks.add_task(
        claim_service.run_claim_pipeline, claim_id, claimant_id, query, raw_documents
    )
    return ClaimSubmitResponse(claim_id=claim_id, status="processing")


@router.get("/{claim_id}", response_model=ClaimStatusResponse)
async def get_claim_status(
    claim_id: str, repository: ClaimRepository = Depends(get_claim_repository)
) -> ClaimStatusResponse:
    claim = repository.get_claim(claim_id)
    return ClaimStatusResponse(
        claim_id=claim.id,
        claimant_id=claim.claimant_id,
        status=claim.status,  # type: ignore[arg-type]
        query=claim.query,
        intent=claim.intent,
        intent_confidence=claim.intent_confidence,
        submitted_at=claim.submitted_at,
    )
