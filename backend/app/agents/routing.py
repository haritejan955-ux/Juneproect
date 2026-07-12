"""Conditional-edge functions and the two small control-flow nodes they
route through. Kept separate from the 9 domain agents because these
functions' job is graph control flow, not claim-processing reasoning — see
docs/langgraph-workflow.md.

Neither `route_after_security` nor `route_after_critic` calls an LLM or
mutates state: LangGraph's `add_conditional_edges` path functions can only
return the next node's name, so `retry_count` is incremented by a tiny
dedicated node (`increment_retry_count`) placed on the retry branch only —
never by the routing predicate itself and never by Answer Synthesizer.
"""

from typing import Literal

from app.core.audit import audit_update
from app.state.graph_state import FinalDecision, GraphState


def route_after_security(state: GraphState) -> Literal["coverage_validator", "blocked"]:
    return "blocked" if state.get("security_flag") else "coverage_validator"


def route_after_critic(
    state: GraphState, score_threshold: float, max_retries: int
) -> Literal["prepare_retry", "final_output"]:
    if state.get("confidence", 0.0) >= score_threshold:
        return "final_output"
    if state.get("retry_count", 0) >= max_retries:
        return "final_output"
    return "prepare_retry"


async def increment_retry_count(state: GraphState) -> dict:
    """The sole place `retry_count` is incremented. It only ever executes on
    the retry branch (guarded by `route_after_critic` above), so a claim
    can never be retried more than `max_retries` times."""
    return {"retry_count": state.get("retry_count", 0) + 1}


async def blocked_node(state: GraphState) -> dict:
    """Terminal node for a confirmed prompt injection. No downstream agent
    (Coverage Validator, Fraud Detector, Synthesizer, Self-Critic) ever runs
    for a blocked claim — this is a hard stop, not a soft warning.

    Detection detail (which heuristic matched, the LLM classifier's
    confidence/reasoning) is not re-read here — Security Checker already
    wrote it into its own audit_log entry (action="blocked_injection"), so
    this node's entry only needs to record that the pipeline halted as a
    result, not restate why."""
    final_decision: FinalDecision = {
        "claim_id": state["claim_id"],
        "status": "blocked",
        "confidence_score": 1.0,
        "low_confidence": False,
        "attorney_flag": False,
        "justification": (
            "This claim was blocked by the Security Checker due to a suspected prompt "
            "injection attempt detected in the submitted documents."
        ),
        "coverage_map": [],
        "fraud_signals": [],
        "citations": [],
        "disclaimer": "",
        "retry_count": state.get("retry_count", 0),
    }
    return {
        "final_decision": final_decision,
        **audit_update(
            "security_checker", "hard_blocked_pipeline", {"claim_id": state["claim_id"]}
        ),
    }
