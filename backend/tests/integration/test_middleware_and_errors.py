"""Request-ID middleware and the two generic exception handlers
(`RequestValidationError`, catch-all `Exception`) registered in
`app.core.exceptions.register_exception_handlers`."""

import uuid

from fastapi.testclient import TestClient

from app.api.dependencies import get_claim_service
from app.main import create_app
from tests.conftest import TEST_API_KEY


def test_request_id_is_generated_and_echoed_in_response_header():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")

    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    # Must be a real generated id, not an empty/placeholder value.
    uuid.UUID(request_id)


def test_client_supplied_request_id_is_preserved_not_replaced():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": "caller-supplied-id-123"})

    assert response.headers["x-request-id"] == "caller-supplied-id-123"


def test_validation_error_returns_structured_error_shape():
    app = create_app()
    with TestClient(app) as client:
        # Missing the required `query` and `files` fields entirely.
        response = client.post(
            "/api/v1/claims",
            headers={"X-API-Key": TEST_API_KEY},
            data={"claimant_id": "claimant-1"},
        )

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "validation_error"
    assert isinstance(body["details"], list)
    assert body["details"]


class _RaisingClaimService:
    async def submit_claim(self, claimant_id: str, query: str, files: list):
        raise RuntimeError("boom — simulated unhandled bug, not a modeled ClaimAgentError")


def test_unhandled_exception_returns_generic_500_and_never_leaks_details():
    app = create_app()
    app.dependency_overrides[get_claim_service] = lambda: _RaisingClaimService()

    # Starlette's exception-handler middleware sends the graceful response and then
    # re-raises the original exception past it (by design — see
    # app/core/middleware.py's docstring), so the default TestClient would surface that
    # exception to the test instead of the response it already delivered to the client.
    # This is the documented way to test that path: see FastAPI's own testing docs.
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/v1/claims",
            headers={"X-API-Key": TEST_API_KEY},
            data={"claimant_id": "claimant-1", "query": "Is this covered?"},
            files={"files": ("claim.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

    assert response.status_code == 500
    body = response.json()
    assert body["error_code"] == "internal_error"
    assert "boom" not in body["message"]
    assert "RuntimeError" not in body["message"]
    assert body["request_id"] == response.headers["x-request-id"]
