"""Short-term memory: LangGraph's checkpointer.

`MemorySaver` is in-process and run-scoped by design — it is the mechanism
for state persisting *between nodes within one claim's processing run*, not
a substitute for the durable SQLite store in `app.memory.repository`. See
docs/memory-architecture.md for the full three-tier explanation and the
upgrade path (`SqliteSaver`) if cross-restart resumability is ever needed.
"""

from langgraph.checkpoint.memory import MemorySaver


def build_checkpointer() -> MemorySaver:
    return MemorySaver()


def thread_config(claim_id: str) -> dict:
    """The `RunnableConfig` passed to `graph.ainvoke`/`astream` — `thread_id`
    is set to `claim_id` so retries within the Self-Critic loop resume the
    same checkpointed thread instead of starting a fresh, empty one."""
    return {"configurable": {"thread_id": claim_id}}
