from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_health_returns_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_reports_database_and_index_checks(monkeypatch, interaction_retriever):
    import app.api.routes.health as health_route

    monkeypatch.setattr(health_route, "get_interaction_retriever", lambda: interaction_retriever)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"] == {"database": True, "interaction_index": True}
