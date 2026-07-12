"""Smoke test: the full app (real DB engine, real chat model/embeddings
client construction, real empty vector stores, compiled graph) must start
up cleanly under the lifespan context manager with no external network
calls — see tests/conftest.py for how a dummy API key makes this safe."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_liveness_check_returns_ok_with_no_auth_required():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["uptime_seconds"] >= 0


def test_readiness_check_reports_database_and_vector_store_checks():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"]["status"] == "ok"
    assert body["checks"]["policy_corpus_index"]["status"] == "ok"
    assert body["checks"]["historical_decisions_index"]["status"] == "ok"
