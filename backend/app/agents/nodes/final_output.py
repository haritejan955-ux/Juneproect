"""[9] Final Output — deterministic assembly, no LLM call.

Reads the accumulated state and produces the single `final_decision`
object the API and frontend consume. See docs/agent-architecture.md.
"""

from collections.abc import Awaitable, Callable

from app.core.audit import audit_update
from app.state.graph_state import FinalDecision, GraphState

AGENT_NAME = "final_output"


def build_final_output_node() -> Callable[[GraphState], Awaitable[dict]]:
    async def final_output(state: GraphState) -> dict:
        final_decision: FinalDecision = {
            "claim_id": state["claim_id"],
            "status": state.get("decision", "denied"),
            "confidence_score": state.get("confidence", 0.0),
            "low_confidence": state.get("low_confidence", False),
            "attorney_flag": state.get("attorney_flag", False),
            "justification": state.get("justification", ""),
            "coverage_map": state.get("coverage", []),
            "fraud_signals": state.get("fraud_signals", []),
            "citations": state.get("citations", []),
            "disclaimer": state.get("disclaimer", ""),
            "retry_count": state.get("retry_count", 0),
        }

        return {
            "final_decision": final_decision,
            **audit_update(
                AGENT_NAME,
                "finalized_decision",
                {
                    "status": final_decision["status"],
                    "attorney_flag": final_decision["attorney_flag"],
                    "low_confidence": final_decision["low_confidence"],
                },
            ),
        }

    return final_output
