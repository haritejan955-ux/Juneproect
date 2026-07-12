"""[9] Final Output — deterministic assembly, no LLM call.

Reads the accumulated state and produces the single `final_decision`
object the API and frontend consume. See docs/agent-architecture.md.
"""

from collections.abc import Awaitable, Callable

from app.core.audit import audit_update
from app.core.exceptions import GraphStateError
from app.core.logging import get_logger
from app.state.graph_state import FinalDecision, GraphState

AGENT_NAME = "final_output"

logger = get_logger(__name__)


def build_final_output_node() -> Callable[[GraphState], Awaitable[dict]]:
    async def final_output(state: GraphState) -> dict:
        claim_id = state.get("claim_id")
        if not claim_id:
            logger.critical(f"{AGENT_NAME}.missing_claim_id")
            raise GraphStateError("final_output reached without claim_id set in state")

        logger.info(f"{AGENT_NAME}.started", extra={"claim_id": claim_id})

        # Defaulting a genuinely-missing `decision` to "denied" (rather than raising) would
        # silently produce a plausible-looking wrong outcome if answer_synthesizer never ran —
        # a graph-wiring bug masquerading as a legitimate denial. That's worse than crashing.
        if "decision" not in state:
            logger.error(f"{AGENT_NAME}.missing_decision", extra={"claim_id": claim_id})
            raise GraphStateError(
                "final_output reached without 'decision' set in state — this indicates "
                "answer_synthesizer did not run or the graph is misconfigured, not a "
                "legitimate denial.",
                claim_id=claim_id,
            )

        final_decision: FinalDecision = {
            "claim_id": claim_id,
            "status": state["decision"],
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

        logger.info(
            f"{AGENT_NAME}.completed",
            extra={
                "claim_id": claim_id,
                "status": final_decision["status"],
                "attorney_flag": final_decision["attorney_flag"],
                "low_confidence": final_decision["low_confidence"],
            },
        )

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
