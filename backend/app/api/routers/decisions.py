from fastapi import APIRouter, Depends

from app.api.auth import require_api_key
from app.api.dependencies import get_claim_repository
from app.core.exceptions import ClaimNotFoundError
from app.memory.repository import ClaimRepository
from app.schemas.decision import (
    CitationResponse,
    CoverageLineItemResponse,
    DecisionResponse,
    FraudSignalResponse,
)

router = APIRouter(
    prefix="/api/v1/claims", tags=["decisions"], dependencies=[Depends(require_api_key)]
)


@router.get("/{claim_id}/decision", response_model=DecisionResponse)
async def get_decision(
    claim_id: str, repository: ClaimRepository = Depends(get_claim_repository)
) -> DecisionResponse:
    decision = repository.get_decision(claim_id)
    if decision is None:
        raise ClaimNotFoundError(f"No decision yet for claim {claim_id}", claim_id=claim_id)

    line_items = repository.get_coverage_line_items(decision.id)
    fraud_signals = repository.get_fraud_signals(decision.id)
    citations = repository.get_citations(decision.id)

    return DecisionResponse(
        claim_id=claim_id,
        status=decision.decision,  # type: ignore[arg-type]
        confidence_score=decision.confidence_score,
        low_confidence=decision.low_confidence_flag,
        attorney_flag=decision.attorney_flag,
        justification=decision.justification,
        coverage_map=[
            CoverageLineItemResponse(
                cpt_code=item.cpt_code,
                diagnosis_code=item.diagnosis_code,
                status=item.status,  # type: ignore[arg-type]
                cited_clause=item.cited_clause,
                amount_billed=item.amount_billed,
                amount_covered=item.amount_covered,
            )
            for item in line_items
        ],
        fraud_signals=[
            FraudSignalResponse(
                signal_type=signal.signal_type,  # type: ignore[arg-type]
                severity=signal.severity,  # type: ignore[arg-type]
                evidence=signal.evidence,
            )
            for signal in fraud_signals
        ],
        citations=[
            CitationResponse(source_doc=c.source_doc, section=c.section, excerpt=c.excerpt)
            for c in citations
        ],
        disclaimer=decision.disclaimer,
        retry_count=decision.retry_count,
        created_at=decision.created_at,
    )
