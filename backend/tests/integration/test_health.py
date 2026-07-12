"""Smoke test: the full app (real DB engine, real chat model/embeddings
client construction, real empty vector stores, compiled graph) must start
up cleanly under the lifespan context manager with no external network
calls — see tests/conftest.py for how a dummy API key makes this safe."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check_returns_ok():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
