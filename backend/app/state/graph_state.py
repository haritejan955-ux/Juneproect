import operator
from typing import Annotated, Any, TypedDict


class GraphState(TypedDict, total=False):
    # Input
    raw_prescription_text: str
    patient_profile: dict[str, Any]

    # Prescription Parser
    medications: list[dict[str, Any]]
    injection_detected: bool
    injection_reason: str | None

    # Drug Normalizer / Patient Profile Loader
    unrecognized_drugs: list[str]

    # Interaction Retriever (RAG)
    interaction_findings: list[dict[str, Any]]

    # Allergy & Contraindication Checker
    allergy_findings: list[dict[str, Any]]

    # Dosage Validator
    dosage_findings: list[dict[str, Any]]

    # Risk Synthesizer
    report: dict[str, Any] | None

    # Self-Critic
    critique: str | None
    critique_approved: bool
    retry_count: int

    # Final Output
    pharmacist_review_flag: bool
    status: str
    error: str | None

    # Cross-cutting: every node appends here; reducer concatenates across nodes.
    audit_log: Annotated[list[dict[str, Any]], operator.add]
