import pytest
from fastapi.testclient import TestClient
from anime_assistant.core.config import Config
from anime_assistant.server.app import create_app


def _mock_config():
    return Config()


def test_ws_flow_integration():
    app = create_app(_mock_config())
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"command": "startListening"})
            msg = ws.receive_json()
            assert msg["type"] == "state" and msg["state"] == "LISTENING"


def test_ws_disconnect_reconnect():
    app = create_app(_mock_config())
    with TestClient(app) as c:
        with c.websocket_connect("/ws") as ws:
            ws.send_json({"command": "startListening"})
            _ = ws.receive_json()
            ws.close()
    # new connection should succeed with IDLE after cancel
    with TestClient(app) as c2:
        with c2.websocket_connect("/ws") as ws2:
            ws2.send_json({"command": "cancel"})
            msg = ws2.receive_json()
            assert msg["state"] == "IDLE"
            assert msg["type"] == "state"
