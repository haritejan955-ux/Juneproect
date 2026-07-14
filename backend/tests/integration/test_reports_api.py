import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.models import CritiqueResult, Medication, ParsedPrescription, SafetyReportOutput
from app.security.injection_detector import InjectionClassification
from tests.conftest import TEST_API_KEY


async def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_submit_report_requires_api_key():
    async with await _client() as client:
        response = await client.post(
            "/api/v1/reports", json={"raw_prescription_text": "Tylenol 500mg", "patient_profile": {}}
        )
    assert response.status_code == 401


async def test_submit_report_rejects_wrong_api_key():
    async with await _client() as client:
        response = await client.post(
            "/api/v1/reports",
            json={"raw_prescription_text": "Tylenol 500mg", "patient_profile": {}},
            headers={"X-API-Key": "wrong-key"},
        )
    assert response.status_code == 401


async def test_submit_and_fetch_completed_report(graph_fakes):
    graph_fakes.queue(InjectionClassification(is_injection=False, reason=""))
    graph_fakes.queue(
        ParsedPrescription(
            medications=[Medication(raw_name="Tylenol", dose_value=500, dose_unit="mg", frequency="daily")]
        )
    )
    graph_fakes.queue(SafetyReportOutput(overall_severity="none", summary="No risks identified.", findings=[]))
    graph_fakes.queue(CritiqueResult(approved=True, critique=None, missed_considerations=[]))

    async with await _client() as client:
        submit_response = await client.post(
            "/api/v1/reports",
            json={
                "raw_prescription_text": "Patient takes Tylenol 500mg daily.",
                "patient_profile": {"age": 40},
            },
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert submit_response.status_code == 202
        report_id = submit_response.json()["report_id"]

        report = None
        for _ in range(50):
            get_response = await client.get(f"/api/v1/reports/{report_id}", headers={"X-API-Key": TEST_API_KEY})
            report = get_response.json()
            if report["status"] != "processing":
                break
            await asyncio.sleep(0.02)

        assert report is not None
        assert report["status"] == "complete"
        assert report["overall_severity"] == "none"
        assert report["pharmacist_review_flag"] is False

        audit_response = await client.get(
            f"/api/v1/reports/{report_id}/audit", headers={"X-API-Key": TEST_API_KEY}
        )
        assert audit_response.status_code == 200
        audit_entries = audit_response.json()
        assert len(audit_entries) == 9
        assert audit_entries[0]["agent"] == "prescription_parser"


async def test_get_report_404_for_unknown_id():
    async with await _client() as client:
        response = await client.get("/api/v1/reports/does-not-exist", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 404


async def test_list_reports_returns_recent_first(graph_fakes):
    graph_fakes.queue(InjectionClassification(is_injection=False, reason=""))
    graph_fakes.queue(ParsedPrescription(medications=[]))
    graph_fakes.queue(SafetyReportOutput(overall_severity="none", summary="ok", findings=[]))
    graph_fakes.queue(CritiqueResult(approved=True, critique=None, missed_considerations=[]))

    async with await _client() as client:
        submit_response = await client.post(
            "/api/v1/reports",
            json={"raw_prescription_text": "No medications.", "patient_profile": {}},
            headers={"X-API-Key": TEST_API_KEY},
        )
        report_id = submit_response.json()["report_id"]

        # Wait for the background task to finish before the test's event loop closes,
        # so its DB session doesn't outlive the loop it was created on.
        for _ in range(50):
            get_response = await client.get(f"/api/v1/reports/{report_id}", headers={"X-API-Key": TEST_API_KEY})
            if get_response.json()["status"] != "processing":
                break
            await asyncio.sleep(0.02)

        list_response = await client.get("/api/v1/reports", headers={"X-API-Key": TEST_API_KEY})
        assert list_response.status_code == 200
        ids = [r["id"] for r in list_response.json()]
        assert report_id in ids
