from typing import Any

from app.core.audit import audit_entry
from app.core.logging import get_logger
from app.schemas.models import PatientProfile
from app.state.graph_state import GraphState

logger = get_logger(__name__)

NODE_NAME = "patient_profile_loader"


def run(state: GraphState) -> dict[str, Any]:
    raw_profile = state.get("patient_profile") or {}
    profile = PatientProfile.model_validate(raw_profile)

    logger.info(
        "patient_profile_loaded",
        extra={
            "detail": {
                "allergy_count": len(profile.allergies),
                "condition_count": len(profile.conditions),
                "renal_function": profile.renal_function,
            }
        },
    )
    return {
        "patient_profile": profile.model_dump(),
        "audit_log": [
            audit_entry(
                NODE_NAME,
                "loaded_patient_profile",
                {"renal_function": profile.renal_function, "hepatic_function": profile.hepatic_function},
            )
        ],
    }
