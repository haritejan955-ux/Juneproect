"""WebSocket auth uses a query param, not the `X-API-Key` header every REST endpoint
uses — see app/api/websocket.py's docstring for why (browsers can't set custom headers
on a WS handshake). These tests exercise that path directly."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import create_app
from tests.conftest import TEST_API_KEY


def test_websocket_connect_without_api_key_is_rejected():
    app = create_app()
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/v1/claims/claim-1/stream"):
                pass
    assert exc_info.value.code == 4401


def test_websocket_connect_with_wrong_api_key_is_rejected():
    app = create_app()
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/v1/claims/claim-1/stream?api_key=wrong-key"):
                pass
    assert exc_info.value.code == 4401


def test_websocket_connect_with_valid_api_key_is_accepted():
    app = create_app()
    with TestClient(app) as client:
        with client.websocket_connect(
            f"/ws/v1/claims/claim-1/stream?api_key={TEST_API_KEY}"
        ) as websocket:
            # Connection accepted — closing from the client side should not raise.
            websocket.close()
