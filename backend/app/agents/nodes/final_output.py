from typing import Any

from app.core.audit import audit_entry
from app.core.logging import get_logger
from app.state.graph_state import GraphState

logger = get_logger(__name__)

NODE_NAME = "final_output"

HIGH_SEVERITY = {"major", "contraindicated"}


def run(state: GraphState) -> dict[str, Any]:
    if state.get("status") == "blocked":
        return {
            "audit_log": [
                audit_entry(NODE_NAME, "terminated_blocked", {"reason": state.get("injection_reason")})
            ],
        }

    report = state.get("report") or {}
    all_findings = (
        state.get("interaction_findings", [])
        + state.get("allergy_findings", [])
        + state.get("dosage_findings", [])
    )
    pharmacist_review_flag = report.get("overall_severity") in HIGH_SEVERITY or any(
        f.get("severity") in HIGH_SEVERITY for f in all_findings
    )

    logger.info(
        "final_output_ready",
        extra={"detail": {"pharmacist_review_flag": pharmacist_review_flag, "retry_count": state.get("retry_count", 0)}},
    )
    return {
        "pharmacist_review_flag": pharmacist_review_flag,
        "status": "complete",
        "audit_log": [
            audit_entry(
                NODE_NAME,
                "finalized_report",
                {"pharmacist_review_flag": pharmacist_review_flag},
            )
        ],
    }
