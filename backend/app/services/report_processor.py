from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.db.models import AuditLogEntry, SafetyReport
from app.db.session import SessionLocal
from app.services.broadcaster import broadcaster
from app.services.graph_runner import run_and_broadcast

logger = get_logger(__name__)


async def process_report(report_id: str, raw_text: str, patient_profile: dict[str, Any]) -> None:
    """Background task kicked off by POST /reports: runs the graph, then persists the
    final state (report fields + full audit trail) to the report's DB row."""
    try:
        final_state = await run_and_broadcast(report_id, raw_text, patient_profile)
    except Exception as exc:  # noqa: BLE001 - persisted as the report's terminal error state
        logger.exception("report_processing_failed", extra={"detail": {"report_id": report_id}})
        async with SessionLocal() as session:
            report = await session.get(SafetyReport, report_id)
            if report is not None:
                report.status = "error"
                report.error = str(exc)
                report.completed_at = datetime.now(timezone.utc)
                await session.commit()
        await broadcaster.publish(report_id, {"type": "complete", "status": "error"})
        return

    report_output = final_state.get("report") or {}
    findings = (
        final_state.get("interaction_findings", [])
        + final_state.get("allergy_findings", [])
        + final_state.get("dosage_findings", [])
    )

    async with SessionLocal() as session:
        report = await session.get(SafetyReport, report_id)
        if report is None:
            return
        report.status = final_state.get("status", "error")
        report.medications = final_state.get("medications", [])
        report.findings = findings
        report.summary = report_output.get("summary")
        report.overall_severity = report_output.get("overall_severity")
        report.pharmacist_review_flag = final_state.get("pharmacist_review_flag", False)
        report.retry_count = final_state.get("retry_count", 0)
        if final_state.get("status") == "blocked":
            report.error = final_state.get("injection_reason")
        report.completed_at = datetime.now(timezone.utc)

        for entry in final_state.get("audit_log", []):
            session.add(
                AuditLogEntry(
                    report_id=report_id,
                    agent=entry["agent"],
                    action=entry["action"],
                    detail=entry["detail"],
                    timestamp=datetime.fromisoformat(entry["timestamp"]),
                )
            )
        await session.commit()
