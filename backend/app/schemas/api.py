from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PatientProfileIn(BaseModel):
    age: int | None = None
    weight_kg: float | None = None
    sex: str | None = None
    allergies: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    renal_function: Literal["normal", "mild", "moderate", "severe"] = "normal"
    hepatic_function: Literal["normal", "mild", "moderate", "severe"] = "normal"


class SubmitReportRequest(BaseModel):
    raw_prescription_text: str
    patient_profile: PatientProfileIn = Field(default_factory=PatientProfileIn)


class SubmitReportResponse(BaseModel):
    report_id: str
    status: str


class SafetyReportResponse(BaseModel):
    id: str
    patient_id: str
    status: str
    overall_severity: str | None
    medications: list[dict[str, Any]]
    findings: list[dict[str, Any]]
    summary: str | None
    pharmacist_review_flag: bool
    retry_count: int
    error: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class AuditEntryResponse(BaseModel):
    timestamp: datetime
    agent: str
    action: str
    detail: dict[str, Any]

    model_config = {"from_attributes": True}


class ReportSummary(BaseModel):
    id: str
    status: str
    overall_severity: str | None
    pharmacist_review_flag: bool
    created_at: datetime

    model_config = {"from_attributes": True}
