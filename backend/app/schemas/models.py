from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["none", "minor", "moderate", "major", "contraindicated"]


class PatientProfile(BaseModel):
    age: int | None = None
    weight_kg: float | None = None
    sex: str | None = None
    allergies: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    renal_function: Literal["normal", "mild", "moderate", "severe"] = "normal"
    hepatic_function: Literal["normal", "mild", "moderate", "severe"] = "normal"


class Medication(BaseModel):
    raw_name: str
    normalized_name: str | None = None
    drug_class: str | None = None
    allergy_class: str | None = None
    dose_value: float | None = None
    dose_unit: str | None = None
    frequency: str | None = None
    route: str | None = None
    recognized: bool = False


class ParsedPrescription(BaseModel):
    """Structured output schema the Prescription Parser LLM call is bound to."""

    medications: list[Medication]


class InteractionFinding(BaseModel):
    category: Literal["interaction"] = "interaction"
    drugs: list[str]
    severity: Severity
    description: str
    citation_doc_id: str
    citation_title: str


class AllergyFinding(BaseModel):
    category: Literal["allergy"] = "allergy"
    drug: str
    allergy_class: str
    severity: Severity
    description: str


class DosageFinding(BaseModel):
    category: Literal["dosage"] = "dosage"
    drug: str
    severity: Severity
    description: str
    recommended_max: str | None = None


class SafetyReportOutput(BaseModel):
    """Structured output schema the Risk Synthesizer LLM call is bound to."""

    overall_severity: Severity
    summary: str
    findings: list[dict]


class CritiqueResult(BaseModel):
    """Structured output schema the Self-Critic LLM call is bound to."""

    approved: bool
    critique: str | None = None
    missed_considerations: list[str] = Field(default_factory=list)
