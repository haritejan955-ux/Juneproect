from typing import Any

from app.core.audit import audit_entry
from app.core.logging import get_logger
from app.data.drug_reference import ALLERGY_CLASS_LABELS, find_drug
from app.state.graph_state import GraphState

logger = get_logger(__name__)

NODE_NAME = "allergy_checker"


def _allergy_conflict(patient_allergy: str, allergy_class: str | None, canonical_name: str) -> bool:
    stated = patient_allergy.strip().lower()
    if stated == canonical_name.lower():
        return True
    if not allergy_class:
        return False
    class_singular = allergy_class.rstrip("s")
    return stated in allergy_class or class_singular in stated or stated in class_singular


def run(state: GraphState) -> dict[str, Any]:
    medications = state.get("medications", [])
    profile = state.get("patient_profile") or {}
    allergies: list[str] = profile.get("allergies", [])
    conditions: list[str] = [c.lower() for c in profile.get("conditions", [])]

    findings: list[dict[str, Any]] = []

    for med in medications:
        if not med.get("recognized"):
            continue
        canonical = med["normalized_name"]

        for patient_allergy in allergies:
            if _allergy_conflict(patient_allergy, med.get("allergy_class"), canonical):
                label = ALLERGY_CLASS_LABELS.get(med.get("allergy_class") or "", canonical)
                findings.append(
                    {
                        "category": "allergy",
                        "drug": canonical,
                        "allergy_class": med.get("allergy_class"),
                        "severity": "contraindicated",
                        "description": (
                            f"Patient has a documented allergy to '{patient_allergy}', which "
                            f"conflicts with {canonical} ({label})."
                        ),
                    }
                )
                break

        record = find_drug(canonical)
        if record:
            for contraindicated_condition in record["contraindicated_conditions"]:
                if any(contraindicated_condition in c or c in contraindicated_condition for c in conditions):
                    findings.append(
                        {
                            "category": "allergy",
                            "drug": canonical,
                            "allergy_class": None,
                            "severity": "major",
                            "description": (
                                f"{canonical} is contraindicated in patients with "
                                f"{contraindicated_condition}, which is on this patient's problem list."
                            ),
                        }
                    )

    logger.info("allergy_check_complete", extra={"detail": {"finding_count": len(findings)}})
    return {
        "allergy_findings": findings,
        "audit_log": [
            audit_entry(NODE_NAME, "checked_allergies_and_contraindications", {"finding_count": len(findings)})
        ],
    }
