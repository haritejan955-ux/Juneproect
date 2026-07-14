from typing import Any, Literal

from app.core.audit import audit_entry
from app.core.config import get_settings
from app.state.graph_state import GraphState

NODE_NAME = "prepare_retry"


def route_after_parser(state: GraphState) -> Literal["blocked", "continue"]:
    return "blocked" if state.get("injection_detected") else "continue"


def route_after_critic(state: GraphState) -> Literal["retry", "final_output"]:
    settings = get_settings()
    if state.get("critique_approved"):
        return "final_output"
    if state.get("retry_count", 0) < settings.max_synthesis_retries:
        return "retry"
    return "final_output"


def prepare_retry(state: GraphState) -> dict[str, Any]:
    """Increments retry_count and clears the approval flag before looping back to the
    Risk Synthesizer with the Self-Critic's critique injected. The dedicated node (as
    opposed to inlining the increment in a conditional edge) keeps the retry_count
    guard visible in the audit log and impossible to bypass."""
    retry_count = state.get("retry_count", 0) + 1
    return {
        "retry_count": retry_count,
        "audit_log": [audit_entry(NODE_NAME, "retrying_synthesis", {"retry_count": retry_count})],
    }
