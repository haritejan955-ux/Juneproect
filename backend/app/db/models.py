import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    sex: Mapped[str | None] = mapped_column(String, nullable=True)
    allergies: Mapped[list[str]] = mapped_column(JSON, default=list)
    conditions: Mapped[list[str]] = mapped_column(JSON, default=list)
    renal_function: Mapped[str] = mapped_column(String, default="normal")
    hepatic_function: Mapped[str] = mapped_column(String, default="normal")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    reports: Mapped[list["SafetyReport"]] = relationship(back_populates="patient")


class SafetyReport(Base):
    __tablename__ = "safety_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    raw_prescription_text: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")
    overall_severity: Mapped[str | None] = mapped_column(String, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    pharmacist_review_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    medications: Mapped[list[dict]] = mapped_column(JSON, default=list)
    findings: Mapped[list[dict]] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="reports")
    audit_entries: Mapped[list["AuditLogEntry"]] = relationship(
        back_populates="report", order_by="AuditLogEntry.timestamp"
    )


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(ForeignKey("safety_reports.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    agent: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)

    report: Mapped["SafetyReport"] = relationship(back_populates="audit_entries")
