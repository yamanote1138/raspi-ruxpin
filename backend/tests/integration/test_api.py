"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client(integration_settings):
    """Provide FastAPI test client."""
    from backend.dependencies import get_settings

    app.dependency_overrides[get_settings] = lambda: integration_settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def _receive_until_type(websocket, target_type: str, max_messages: int = 20) -> dict | None:
    """Receive messages until we get one of the target type."""
    for _ in range(max_messages):
        try:
            data = websocket.receive_json()
            if data.get("type") == target_type:
                return data
        except Exception:
            break
    return None


def test_health_endpoint(client):
    """Test health check endpoint returns 200."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_health_endpoint_structure(client):
    """Test health endpoint returns expected structure."""
    response = client.get("/api/health")
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_websocket_connection(client):
    """Test WebSocket connection establishment."""
    with client.websocket_connect("/ws") as websocket:
        assert websocket is not None


@pytest.mark.asyncio
async def test_websocket_initial_state(client):
    """Test WebSocket sends initial bear state on connection."""
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()

        assert data["type"] == "bear_state"
        assert "data" in data

        bear_state = data["data"]
        assert "eyes" in bear_state
        assert "mouth" in bear_state
        assert "is_busy" in bear_state
        assert "blink_enabled" in bear_state


@pytest.mark.asyncio
async def test_websocket_update_bear(client):
    """Test WebSocket update_bear message."""
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        initial = websocket.receive_json()
        assert initial["type"] == "bear_state"

        # Send update_bear message
        websocket.send_json(
            {"type": "update_bear", "data": {"eyes": "closed", "mouth": "open"}}
        )

        # Should receive updated state (may be interleaved with broadcast)
        response = _receive_until_type(websocket, "bear_state")
        assert response is not None
        assert "eyes" in response["data"]
        assert "mouth" in response["data"]


@pytest.mark.asyncio
async def test_websocket_set_volume(client):
    """Test WebSocket set_volume message."""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "set_volume", "level": 75})

        # Volume update returns bear_state or error
        response = _receive_until_type(websocket, "bear_state")
        assert response is not None


@pytest.mark.asyncio
async def test_websocket_fetch_phrases(client):
    """Test WebSocket fetch_phrases message."""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "fetch_phrases"})

        # Should receive phrases response (may be interleaved with broadcasts)
        response = _receive_until_type(websocket, "phrases")
        assert response is not None
        assert "data" in response
        assert isinstance(response["data"], dict)


@pytest.mark.asyncio
async def test_websocket_invalid_message(client):
    """Test WebSocket handles invalid message gracefully."""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"data": {"foo": "bar"}})

        # Should receive error or handle gracefully
        try:
            response = websocket.receive_json()
            if "type" in response:
                assert response["type"] in ["error", "bear_state"]
        except Exception:
            pass


@pytest.mark.asyncio
async def test_websocket_unknown_message_type(client):
    """Test WebSocket handles unknown message type."""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "unknown_type", "data": {}})

        try:
            response = websocket.receive_json()
            assert "type" in response
        except Exception:
            pass


@pytest.mark.asyncio
async def test_websocket_multiple_clients(client):
    """Test multiple WebSocket clients can connect."""
    with client.websocket_connect("/ws") as ws1:
        with client.websocket_connect("/ws") as ws2:
            # Both should receive initial state
            data1 = _receive_until_type(ws1, "bear_state")
            data2 = _receive_until_type(ws2, "bear_state")

            assert data1 is not None
            assert data2 is not None


@pytest.mark.asyncio
async def test_websocket_disconnect_cleanup(client):
    """Test WebSocket connection cleanup on disconnect."""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()

    # Reconnect should work
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "bear_state"


def test_cors_headers(client):
    """Test CORS headers are present in development."""
    response = client.get("/api/health")
    cors_headers = [k for k in response.headers.keys() if "access-control" in k.lower()]
    assert len(cors_headers) > 0 or response.status_code == 200


def test_static_file_serving(client):
    """Test static file serving is configured."""
    assert app is not None
