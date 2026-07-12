"""WS /ws/v1/claims/{claim_id}/stream — live per-agent status.

One event per completed LangGraph node (see app.services.streaming and
app.services.claim_service), not token-level model output — see
docs/api-architecture.md section 3 for why.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.streaming import StreamPublisher

router = APIRouter()


@router.websocket("/ws/v1/claims/{claim_id}/stream")
async def claim_stream(websocket: WebSocket, claim_id: str) -> None:
    stream_publisher: StreamPublisher = websocket.app.state.stream_publisher
    await websocket.accept()
    await stream_publisher.subscribe(claim_id, websocket)
    try:
        while True:
            # The client doesn't need to send anything; reading here just lets
            # us detect a disconnect promptly instead of leaking the socket.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await stream_publisher.unsubscribe(claim_id, websocket)
