import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.auth import require_api_key
from app.api.dependencies import get_dispute_service
from app.schemas.dispute import (
    DisputeMessageRequest,
    DisputeMessageResponse,
    DisputeThreadResponse,
)
from app.services.dispute_service import DisputeService

router = APIRouter(
    prefix="/api/v1/claims", tags=["disputes"], dependencies=[Depends(require_api_key)]
)


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


def _format_sse(event: dict) -> str:
    return f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"


@router.post("/{claim_id}/dispute/stream")
async def stream_dispute_message(
    claim_id: str,
    payload: DisputeMessageRequest,
    dispute_service: DisputeService = Depends(get_dispute_service),
) -> StreamingResponse:
    """Server-Sent Events version of `POST /dispute`: the same reply, delivered as it's
    generated instead of as one blocking response. See `DisputeService.stream_message` for
    why token-level streaming is safe here but was deliberately rejected for the claim
    pipeline's WS stream.

    The generator's first item is fetched *before* constructing the `StreamingResponse` —
    once a streaming response starts, its 200 status and headers are already on the wire, so
    an exception raised mid-stream (e.g. `ClaimNotFoundError` for a bad `claim_id`) can no
    longer become a proper 404 JSON error. Forcing that failure to happen here instead lets
    it flow through the normal exception handlers like every other endpoint.
    """
    events = dispute_service.stream_message(claim_id, payload.message)
    first_event = await events.__anext__()

    async def event_source():
        yield _format_sse(first_event)
        async for event in events:
            yield _format_sse(event)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
