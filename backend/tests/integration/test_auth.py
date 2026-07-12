"""API key authentication — exercised against the real app (real lifespan, no service
fakes) since auth is enforced by router-level middleware/dependencies, not anything a
service-layer fake could bypass or accidentally satisfy."""

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import TEST_API_KEY


def test_protected_endpoint_without_api_key_is_rejected():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/claims/some-claim-id")

    assert response.status_code == 401
    assert response.json()["error_code"] == "unauthorized"


def test_protected_endpoint_with_wrong_api_key_is_rejected():
    app = create_app()
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/claims/some-claim-id", headers={"X-API-Key": "not-the-right-key"}
        )

    assert response.status_code == 401


def test_protected_endpoint_with_valid_api_key_is_not_rejected_for_auth():
    """A valid key should clear the auth gate — the request still 404s because the claim
    doesn't exist, which is the point: that's a *different* failure than 401, proving the
    request actually reached the route handler."""
    app = create_app()
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/claims/nonexistent-claim", headers={"X-API-Key": TEST_API_KEY}
        )

    assert response.status_code == 404
    assert response.json()["error_code"] == "claim_not_found"


def test_health_endpoints_require_no_api_key():
    app = create_app()
    with TestClient(app) as client:
        liveness = client.get("/health")
        readiness = client.get("/health/ready")

    assert liveness.status_code == 200
    assert readiness.status_code == 200


def test_openapi_schema_declares_api_key_security_scheme():
    """Confirms the Swagger "Authorize" button is actually wired, not just that auth
    happens to work at the HTTP layer."""
    app = create_app()
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    security_schemes = schema["components"]["securitySchemes"]
    assert "APIKeyHeader" in security_schemes
    assert security_schemes["APIKeyHeader"]["in"] == "header"
    assert security_schemes["APIKeyHeader"]["name"] == "X-API-Key"

    claims_get = schema["paths"]["/api/v1/claims/{claim_id}"]["get"]
    assert any("APIKeyHeader" in requirement for requirement in claims_get["security"])
