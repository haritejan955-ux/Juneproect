"""HTTP-contract tests for the SSE dispute-streaming endpoint, with
`get_dispute_service` faked — same pattern as `test_claims_api.py`. This is about the
endpoint's framing (SSE format, status codes) and the "prime the generator before
constructing StreamingResponse" behavior, not about a real chat model."""

from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.api.dependencies import get_dispute_service
from app.core.exceptions import ClaimNotFoundError
from app.main import create_app
from tests.conftest import TEST_API_KEY


class _FakeStreamingDisputeService:
    def __init__(self, events: list[dict] | None = None, error: Exception | None = None) -> None:
        self._events = events or []
        self._error = error

    async def stream_message(self, claim_id: str, message: str) -> AsyncIterator[dict]:
        if self._error is not None:
            raise self._error
        for event in self._events:
            yield event


def test_stream_dispute_message_returns_sse_formatted_events():
    app = create_app()
    fake_service = _FakeStreamingDisputeService(
        events=[
            {"event": "token", "data": {"content": "Your claim "}},
            {"event": "token", "data": {"content": "was reviewed."}},
            {"event": "done", "data": {"id": "msg-1", "timestamp": "2026-01-01T00:00:00+00:00"}},
        ]
    )
    app.dependency_overrides[get_dispute_service] = lambda: fake_service

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/claims/claim-1/dispute/stream",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": "Why was my claim denied?"},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: token" in body
    assert 'data: {"content": "Your claim "}' in body
    assert "event: done" in body
    assert '"id": "msg-1"' in body


def test_stream_dispute_message_surfaces_claim_not_found_as_404_not_a_broken_stream():
    """The generator is primed before `StreamingResponse` is constructed specifically so
    this case becomes a normal JSON 404, not a 200 that then produces zero bytes."""
    app = create_app()
    fake_service = _FakeStreamingDisputeService(
        error=ClaimNotFoundError("No finalized decision exists for claim x", claim_id="x")
    )
    app.dependency_overrides[get_dispute_service] = lambda: fake_service

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/claims/x/dispute/stream",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": "hello"},
        )

    assert response.status_code == 404
    assert response.json()["error_code"] == "claim_not_found"


def test_stream_dispute_message_requires_api_key():
    app = create_app()
    app.dependency_overrides[get_dispute_service] = lambda: _FakeStreamingDisputeService()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/claims/claim-1/dispute/stream", json={"message": "hello"}
        )

    assert response.status_code == 401
