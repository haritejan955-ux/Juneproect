from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.audit import audit_entry
from app.core.llm import get_chat_model
from app.core.logging import get_logger
from app.prompts.prescription_parser_prompt import SYSTEM_PROMPT
from app.schemas.models import ParsedPrescription
from app.security.injection_detector import detect_injection
from app.state.graph_state import GraphState

logger = get_logger(__name__)

NODE_NAME = "prescription_parser"


def run(state: GraphState) -> dict[str, Any]:
    raw_text = state["raw_prescription_text"]
    llm = get_chat_model()

    is_injection, reason = detect_injection(raw_text, llm)
    if is_injection:
        logger.warning("prescription_injection_blocked", extra={"detail": {"reason": reason}})
        return {
            "injection_detected": True,
            "injection_reason": reason,
            "status": "blocked",
            "medications": [],
            "audit_log": [
                audit_entry(NODE_NAME, "blocked_prompt_injection", {"reason": reason})
            ],
        }

    parser = llm.with_structured_output(ParsedPrescription)
    parsed = parser.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=raw_text),
        ]
    )
    assert isinstance(parsed, ParsedPrescription)
    medications = [m.model_dump() for m in parsed.medications]

    logger.info("prescription_parsed", extra={"detail": {"medication_count": len(medications)}})
    return {
        "injection_detected": False,
        "injection_reason": None,
        "medications": medications,
        "audit_log": [
            audit_entry(
                NODE_NAME, "parsed_medications", {"medication_count": len(medications)}
            )
        ],
    }
