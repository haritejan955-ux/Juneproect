import itertools
from typing import Any

from app.core.audit import audit_entry
from app.core.logging import get_logger
from app.rag.dependency import get_interaction_retriever
from app.state.graph_state import GraphState

logger = get_logger(__name__)

NODE_NAME = "interaction_retriever"


def _summary(text: str) -> str:
    paragraphs = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    return paragraphs[2] if len(paragraphs) >= 3 else text.strip()[:300]


def _unique_drug_names(medications: list[dict[str, Any]]) -> list[str]:
    names = {
        m["normalized_name"].lower() for m in medications if m.get("recognized") and m.get("normalized_name")
    }
    return sorted(names)


def run(state: GraphState) -> dict[str, Any]:
    medications = state.get("medications", [])
    names = _unique_drug_names(medications)
    retriever = get_interaction_retriever()

    findings: list[dict[str, Any]] = []
    seen_doc_ids: set[str] = set()

    for drug_a, drug_b in itertools.combinations(names, 2):
        query = f"{drug_a} and {drug_b} drug interaction"
        hits = retriever.search(query, k=5)
        for hit in hits:
            pair = {p.lower() for p in hit["drug_pair"]}
            if drug_a in pair and drug_b in pair and hit["doc_id"] not in seen_doc_ids:
                seen_doc_ids.add(hit["doc_id"])
                findings.append(
                    {
                        "category": "interaction",
                        "drugs": [drug_a, drug_b],
                        "severity": hit["severity"],
                        "description": _summary(hit["text"]),
                        "citation_doc_id": hit["doc_id"],
                        "citation_title": hit["title"],
                    }
                )
                break

    logger.info("interactions_retrieved", extra={"detail": {"finding_count": len(findings)}})
    return {
        "interaction_findings": findings,
        "audit_log": [
            audit_entry(NODE_NAME, "retrieved_interactions", {"finding_count": len(findings)})
        ],
    }
