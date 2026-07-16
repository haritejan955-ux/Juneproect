import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.audit import audit_entry
from app.core.llm import get_chat_model
from app.core.logging import get_logger
from app.prompts.self_critic_prompt import SYSTEM_PROMPT
from app.schemas.models import CritiqueResult
from app.state.graph_state import GraphState

logger = get_logger(__name__)

NODE_NAME = "self_critic"


def run(state: GraphState) -> dict[str, Any]:
    llm = get_chat_model()
    critic = llm.with_structured_output(CritiqueResult)

    payload = {
        "report": state.get("report"),
        "interaction_findings": state.get("interaction_findings", []),
        "allergy_findings": state.get("allergy_findings", []),
        "dosage_findings": state.get("dosage_findings", []),
    }

    result = critic.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(payload, indent=2)),
        ]
    )
    assert isinstance(result, CritiqueResult)

    logger.info(
        "self_critique_complete",
        extra={"detail": {"approved": result.approved, "missed": result.missed_considerations}},
    )
    return {
        "critique_approved": result.approved,
        "critique": None if result.approved else result.critique,
        "audit_log": [
            audit_entry(
                NODE_NAME,
                "reviewed_report",
                {"approved": result.approved, "missed_considerations": result.missed_considerations},
            )
        ],
    }
