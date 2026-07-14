import asyncio
from collections import defaultdict
from typing import Any


class ReportProgressBroadcaster:
    """In-process pub/sub of per-report progress events for the WebSocket endpoint.

    Single-process only (matches the single-writer SQLite deployment model): fine for
    the one-backend-instance deployment this project targets.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, report_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[report_id].append(queue)
        return queue

    def unsubscribe(self, report_id: str, queue: asyncio.Queue) -> None:
        subs = self._subscribers.get(report_id)
        if subs and queue in subs:
            subs.remove(queue)
        if subs is not None and not subs:
            self._subscribers.pop(report_id, None)

    async def publish(self, report_id: str, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers.get(report_id, [])):
            await queue.put(event)


broadcaster = ReportProgressBroadcaster()
