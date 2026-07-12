"""WS /ws/v1/claims/{claim_id}/stream — live per-agent status.

One event per completed LangGraph node (see app.services.streaming and
app.services.claim_service), not token-level model output — see
docs/api-architecture.md section 3 for why.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config.settings import get_settings
from app.services.streaming import StreamPublisher

router = APIRouter()

_UNAUTHORIZED_CLOSE_CODE = 4401
"""In the 4000-4999 application-reserved range (RFC 6455 section 7.4.2) — a plain WS close
handshake has no room for an HTTP-style status code or body, so this is the only way to
signal "you weren't authorized" rather than an ambiguous disconnect."""


@router.websocket("/ws/v1/claims/{claim_id}/stream")
async def claim_stream(websocket: WebSocket, claim_id: str) -> None:
    """Auth is a query param (`?api_key=...`), not the `X-API-Key` header every REST
    endpoint uses: the browser `WebSocket` API cannot set custom headers on the connect
    handshake, so the header-based scheme in `app.api.auth` isn't reachable from here."""
    settings = get_settings()
    api_key = websocket.query_params.get("api_key")
    if not api_key or api_key not in settings.api_keys:
        await websocket.close(code=_UNAUTHORIZED_CLOSE_CODE, reason="Missing or invalid API key")
        return

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
