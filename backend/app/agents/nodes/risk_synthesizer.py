import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.audit import audit_entry
from app.core.llm import get_chat_model
from app.core.logging import get_logger
from app.prompts.risk_synthesizer_prompt import SYSTEM_PROMPT, build_critique_context
from app.schemas.models import SafetyReportOutput
from app.state.graph_state import GraphState

logger = get_logger(__name__)

NODE_NAME = "risk_synthesizer"


def run(state: GraphState) -> dict[str, Any]:
    llm = get_chat_model()
    synthesizer = llm.with_structured_output(SafetyReportOutput)

    payload = {
        "medications": state.get("medications", []),
        "patient_profile": state.get("patient_profile", {}),
        "interaction_findings": state.get("interaction_findings", []),
        "allergy_findings": state.get("allergy_findings", []),
        "dosage_findings": state.get("dosage_findings", []),
    }
    human_content = json.dumps(payload, indent=2) + "\n\n" + build_critique_context(state.get("critique"))

    result = synthesizer.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=human_content),
        ]
    )
    assert isinstance(result, SafetyReportOutput)

    logger.info(
        "report_synthesized",
        extra={"detail": {"overall_severity": result.overall_severity, "retry_count": state.get("retry_count", 0)}},
    )
    return {
        "report": result.model_dump(),
        "audit_log": [
            audit_entry(
                NODE_NAME,
                "synthesized_report",
                {"overall_severity": result.overall_severity, "retry_count": state.get("retry_count", 0)},
            )
        ],
    }
