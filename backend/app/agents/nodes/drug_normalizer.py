from typing import Any

from app.core.audit import audit_entry
from app.core.logging import get_logger
from app.data.drug_reference import find_drug
from app.state.graph_state import GraphState

logger = get_logger(__name__)

NODE_NAME = "drug_normalizer"


def run(state: GraphState) -> dict[str, Any]:
    medications = state.get("medications", [])
    normalized: list[dict[str, Any]] = []
    unrecognized: list[str] = []

    for med in medications:
        record = find_drug(med["raw_name"])
        med = dict(med)
        if record:
            med["normalized_name"] = record["canonical_name"]
            med["drug_class"] = record["drug_class"]
            med["allergy_class"] = record["allergy_class"]
            med["recognized"] = True
        else:
            med["recognized"] = False
            unrecognized.append(med["raw_name"])
        normalized.append(med)

    logger.info(
        "drugs_normalized",
        extra={"detail": {"recognized": len(normalized) - len(unrecognized), "unrecognized": unrecognized}},
    )
    return {
        "medications": normalized,
        "unrecognized_drugs": unrecognized,
        "audit_log": [
            audit_entry(
                NODE_NAME,
                "normalized_medications",
                {"recognized_count": len(normalized) - len(unrecognized), "unrecognized": unrecognized},
            )
        ],
    }
