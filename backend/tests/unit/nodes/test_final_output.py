"""Unit tests for [9] Final Output."""

import pytest

from app.agents.nodes.final_output import build_final_output_node
from app.core.exceptions import GraphStateError
from app.state.graph_state import GraphState


async def test_assembles_final_decision_from_accumulated_state():
    node = build_final_output_node()
    state: GraphState = {
        "claim_id": "c1",
        "decision": "partial_approved",
        "confidence": 0.85,
        "low_confidence": False,
        "attorney_flag": False,
        "justification": "Line-item 1 approved, line-item 2 denied.",
        "coverage": [],
        "fraud_signals": [],
        "citations": [],
        "disclaimer": "Consult a licensed adjuster.",
        "retry_count": 1,
    }

    result = await node(state)

    final = result["final_decision"]
    assert final["claim_id"] == "c1"
    assert final["status"] == "partial_approved"
    assert final["confidence_score"] == 0.85
    assert final["retry_count"] == 1
    assert result["audit_log"][0]["action"] == "finalized_decision"


async def test_missing_decision_raises_graph_state_error_instead_of_defaulting():
    """A missing `decision` must never silently become "denied" — that would
    make a graph-wiring bug indistinguishable from a legitimate denial."""
    node = build_final_output_node()
    state: GraphState = {"claim_id": "c1"}

    with pytest.raises(GraphStateError):
        await node(state)


async def test_missing_claim_id_raises_graph_state_error():
    node = build_final_output_node()
    state: GraphState = {"decision": "approved"}

    with pytest.raises(GraphStateError):
        await node(state)
