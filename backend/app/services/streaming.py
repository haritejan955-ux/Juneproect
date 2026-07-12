"""Bridges LangGraph per-node events to WebSocket clients subscribed to a
given claim_id. In-memory only — matches the single-process deployment
this system targets; see docs/api-architecture.md section 3.
"""

import asyncio
from collections import defaultdict

from fastapi import WebSocket

from app.core.logging import get_logger

logger = get_logger(__name__)


class StreamPublisher:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, claim_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[claim_id].append(websocket)

    async def unsubscribe(self, claim_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            sockets = self._connections.get(claim_id)
            if sockets and websocket in sockets:
                sockets.remove(websocket)

    async def publish(self, claim_id: str, event: dict) -> None:
        async with self._lock:
            sockets = list(self._connections.get(claim_id, []))
        for socket in sockets:
            try:
                await socket.send_json(event)
            except Exception:
                logger.warning("Failed to publish stream event; dropping subscriber")
                await self.unsubscribe(claim_id, socket)

    async def close(self, claim_id: str) -> None:
        async with self._lock:
            self._connections.pop(claim_id, None)
