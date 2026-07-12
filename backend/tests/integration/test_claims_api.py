"""Exercises the HTTP contract of claim submission with the real app
lifespan, but with `get_claim_service` overridden to a fake — the real
service would run the full 9-node LLM pipeline as a background task, which
needs live model access and isn't something a CI-safe unit test should
depend on. This test is about the API contract, not agent correctness."""

from fastapi.testclient import TestClient

from app.api.dependencies import get_claim_service
from app.main import create_app
from app.state.graph_state import RawDocument


class _FakeClaimService:
    def __init__(self) -> None:
        self.pipeline_calls: list[tuple] = []

    async def submit_claim(self, claimant_id: str, query: str, files: list) -> tuple[str, list]:
        raw_documents: list[RawDocument] = []
        return "fake-claim-id", raw_documents

    async def run_claim_pipeline(
        self, claim_id: str, claimant_id: str, query: str, raw_documents: list
    ) -> None:
        self.pipeline_calls.append((claim_id, claimant_id, query, raw_documents))


def test_submit_claim_returns_202_with_claim_id():
    app = create_app()
    fake_service = _FakeClaimService()
    app.dependency_overrides[get_claim_service] = lambda: fake_service

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/claims",
            data={"claimant_id": "claimant-1", "query": "Is my MRI covered?"},
            files={"files": ("claim.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        )

    assert response.status_code == 202
    body = response.json()
    assert body["claim_id"] == "fake-claim-id"
    assert body["status"] == "processing"
    assert fake_service.pipeline_calls, "background task should have been scheduled"
