import re
from typing import Any

from app.core.audit import audit_entry
from app.core.logging import get_logger
from app.data.drug_reference import find_drug
from app.state.graph_state import GraphState

logger = get_logger(__name__)

NODE_NAME = "dosage_validator"


def _base_unit(unit: str) -> str:
    return re.sub(r"/.*$", "", unit.strip().lower())


def _renal_severity(note: str) -> str:
    lowered = note.lower()
    if "contraindicated" in lowered:
        return "contraindicated"
    if "avoid" in lowered:
        return "major"
    return "moderate"


def run(state: GraphState) -> dict[str, Any]:
    medications = state.get("medications", [])
    profile = state.get("patient_profile") or {}
    renal_function = profile.get("renal_function", "normal")

    findings: list[dict[str, Any]] = []

    for med in medications:
        if not med.get("recognized"):
            continue
        canonical = med["normalized_name"]
        record = find_drug(canonical)
        if not record:
            continue

        dose_value = med.get("dose_value")
        dose_unit = med.get("dose_unit")
        dose_range = record["adult_dose_range"]
        if dose_value is not None and dose_unit and _base_unit(dose_unit) == _base_unit(dose_range["unit"]):
            if dose_value > dose_range["max"]:
                findings.append(
                    {
                        "category": "dosage",
                        "drug": canonical,
                        "severity": "major",
                        "description": (
                            f"{canonical} {dose_value}{dose_unit} exceeds the typical adult "
                            f"maximum of {dose_range['max']} {dose_range['unit']}."
                        ),
                        "recommended_max": f"{dose_range['max']} {dose_range['unit']}",
                    }
                )
            elif dose_value < dose_range["min"]:
                findings.append(
                    {
                        "category": "dosage",
                        "drug": canonical,
                        "severity": "minor",
                        "description": (
                            f"{canonical} {dose_value}{dose_unit} is below the typical adult "
                            f"minimum of {dose_range['min']} {dose_range['unit']}; verify intent."
                        ),
                        "recommended_max": None,
                    }
                )

        renal_note = record["renal_adjustment"].get(renal_function)
        if renal_note:
            findings.append(
                {
                    "category": "dosage",
                    "drug": canonical,
                    "severity": _renal_severity(renal_note),
                    "description": (
                        f"Patient has {renal_function} renal impairment. {canonical}: {renal_note}"
                    ),
                    "recommended_max": None,
                }
            )

    logger.info("dosage_validation_complete", extra={"detail": {"finding_count": len(findings)}})
    return {
        "dosage_findings": findings,
        "audit_log": [
            audit_entry(NODE_NAME, "validated_dosages", {"finding_count": len(findings)})
        ],
    }
