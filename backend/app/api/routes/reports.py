import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_api_key
from app.core.config import get_settings
from app.db.models import AuditLogEntry, Patient, SafetyReport
from app.db.session import SessionLocal, get_session
from app.schemas.api import (
    AuditEntryResponse,
    ReportSummary,
    SafetyReportResponse,
    SubmitReportRequest,
    SubmitReportResponse,
)
from app.services.broadcaster import broadcaster
from app.services.report_processor import process_report

router = APIRouter(prefix="/api/v1/reports", tags=["reports"], dependencies=[Depends(require_api_key)])

ws_router = APIRouter(tags=["reports-ws"])


@router.post("", response_model=SubmitReportResponse, status_code=202)
async def submit_report(
    payload: SubmitReportRequest, session: AsyncSession = Depends(get_session)
) -> SubmitReportResponse:
    patient = Patient(**payload.patient_profile.model_dump())
    session.add(patient)
    await session.flush()

    report = SafetyReport(
        patient_id=patient.id,
        raw_prescription_text=payload.raw_prescription_text,
        status="processing",
    )
    session.add(report)
    await session.commit()

    asyncio.create_task(
        process_report(report.id, payload.raw_prescription_text, payload.patient_profile.model_dump())
    )

    return SubmitReportResponse(report_id=report.id, status=report.status)


@router.get("", response_model=list[ReportSummary])
async def list_reports(
    limit: int = Query(default=20, le=100), session: AsyncSession = Depends(get_session)
) -> list[SafetyReport]:
    result = await session.execute(
        select(SafetyReport).order_by(SafetyReport.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{report_id}", response_model=SafetyReportResponse)
async def get_report(report_id: str, session: AsyncSession = Depends(get_session)) -> SafetyReport:
    report = await session.get(SafetyReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/audit", response_model=list[AuditEntryResponse])
async def get_report_audit(report_id: str, session: AsyncSession = Depends(get_session)) -> list[AuditLogEntry]:
    report = await session.get(SafetyReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    result = await session.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.report_id == report_id)
        .order_by(AuditLogEntry.timestamp)
    )
    return list(result.scalars().all())


@ws_router.websocket("/ws/reports/{report_id}")
async def report_progress_ws(websocket: WebSocket, report_id: str) -> None:
    settings = get_settings()
    api_key = websocket.query_params.get("api_key")
    if not settings.api_keys or api_key not in settings.api_keys:
        await websocket.close(code=4401)
        return

    await websocket.accept()

    async with SessionLocal() as session:
        report = await session.get(SafetyReport, report_id)

    if report is None:
        await websocket.send_json({"type": "error", "message": "Report not found"})
        await websocket.close()
        return

    if report.status in ("complete", "blocked", "error"):
        await websocket.send_json({"type": "complete", "status": report.status})
        await websocket.close()
        return

    queue = broadcaster.subscribe(report_id)
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
            if event.get("type") == "complete":
                break
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.unsubscribe(report_id, queue)
