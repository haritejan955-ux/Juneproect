import asyncio
import threading
from functools import lru_cache
from typing import Any

from langgraph.graph.state import CompiledStateGraph

from app.agents.graph import build_safety_graph, initial_state
from app.services.broadcaster import broadcaster
from app.state.graph_state import GraphState

_SENTINEL = object()


@lru_cache
def get_graph() -> CompiledStateGraph:
    return build_safety_graph()


async def run_and_broadcast(report_id: str, raw_text: str, patient_profile: dict[str, Any]) -> GraphState:
    """Run the safety graph, publishing a progress event to the report's subscribers
    after every node completes, and return the final merged state.

    LangGraph's own node execution is synchronous (LLM calls go through the sync
    langchain client), so it runs on a worker thread; results are relayed back to the
    event loop through a queue rather than blocking it.
    """
    graph = get_graph()
    state = initial_state(raw_text, patient_profile)
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def _run() -> None:
        try:
            for snapshot in graph.stream(state, stream_mode="values"):
                loop.call_soon_threadsafe(queue.put_nowait, snapshot)
        except Exception as exc:  # noqa: BLE001 - relayed to the event loop, not swallowed
            loop.call_soon_threadsafe(queue.put_nowait, {"__error__": str(exc)})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, _SENTINEL)

    threading.Thread(target=_run, daemon=True).start()

    final_state: GraphState = state
    while True:
        item = await queue.get()
        if item is _SENTINEL:
            break
        if "__error__" in item:
            raise RuntimeError(item["__error__"])
        final_state = item
        audit_log = final_state.get("audit_log") or []
        last_entry = audit_log[-1] if audit_log else None
        await broadcaster.publish(
            report_id,
            {
                "type": "progress",
                "agent": last_entry["agent"] if last_entry else None,
                "action": last_entry["action"] if last_entry else None,
            },
        )

    await broadcaster.publish(
        report_id, {"type": "complete", "status": final_state.get("status", "error")}
    )
    return final_state
