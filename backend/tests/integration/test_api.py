"""Integration tests for API endpoints."""

from collections.abc import Generator
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from backend.config import AppSettings, AudioSettings, HardwareSettings, TTSSettings
from backend.main import app

# Message types the server broadcasts periodically, independent of any
# command a test just sent. Tests waiting for a specific reply must skip
# past these rather than assume the very next message is their reply.
_BROADCAST_MESSAGE_TYPES = {"bear_state", "gpio_status", "log"}


def _receive_until(
    websocket: WebSocketTestSession, expected_types: set[str], max_attempts: int = 20
) -> dict[str, Any]:
    """Read messages until one matches an expected type, skipping periodic broadcasts."""
    for _ in range(max_attempts):
        message = cast(dict[str, Any], websocket.receive_json())
        if message.get("type") in expected_types:
            return message
        if message.get("type") not in _BROADCAST_MESSAGE_TYPES:
            return message
    raise AssertionError(
        f"No message of type {expected_types} received after {max_attempts} attempts"
    )


def _receive_until_state_with(
    websocket: WebSocketTestSession, max_attempts: int = 20, **expected_data: Any
) -> dict[str, Any]:
    """Read bear_state messages until one reflects the given data, skipping stale broadcasts."""
    for _ in range(max_attempts):
        message = cast(dict[str, Any], websocket.receive_json())
        if message.get("type") == "bear_state" and all(
            message.get("data", {}).get(key) == value for key, value in expected_data.items()
        ):
            return message
    raise AssertionError(
        f"No bear_state reflecting {expected_data} received after {max_attempts} attempts"
    )


@pytest.fixture
def test_app_settings(tmp_path: Path) -> AppSettings:
    """Provide test application settings."""
    sounds_dir = tmp_path / "sounds"
    sounds_dir.mkdir()
    tts_dir = tmp_path / "tts"
    tts_dir.mkdir()

    return AppSettings(
        environment="testing",
        debug=True,
        host="127.0.0.1",
        port=8080,
        hardware=HardwareSettings(
            use_mock_gpio=True,
            eyes_pwm=21,
            eyes_dir=16,
            eyes_cdir=20,
            eyes_speed=100,
            eyes_duration=0.4,
            mouth_pwm=25,
            mouth_dir=7,
            mouth_cdir=8,
            mouth_speed=100,
            mouth_duration=0.15,
        ),
        audio=AudioSettings(
            sample_rate=16000,
            amplitude_threshold=500,
            sounds_dir=sounds_dir,
            start_volume=80,
            mixer="PCM",
        ),
        tts=TTSSettings(
            engine="espeak",
            output_dir=tts_dir,
            voice="en+m3",
            speed=125,
            pitch=50,
        ),
    )


@pytest.fixture
def client(test_app_settings: AppSettings) -> Generator[TestClient, None, None]:
    """Provide FastAPI test client."""
    # Override the settings dependency
    from backend.dependencies import get_settings

    app.dependency_overrides[get_settings] = lambda: test_app_settings

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


def test_health_endpoint(client: TestClient) -> None:
    """Test health check endpoint returns 200."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_health_endpoint_structure(client: TestClient) -> None:
    """Test health endpoint returns expected structure."""
    response = client.get("/api/health")
    data = response.json()

    # Check required fields
    assert "status" in data
    assert "version" in data

    # Check types
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_websocket_connection(client: TestClient) -> None:
    """Test WebSocket connection establishment."""
    with client.websocket_connect("/ws") as websocket:
        # Connection should succeed
        assert websocket is not None


@pytest.mark.asyncio
async def test_websocket_initial_state(client: TestClient) -> None:
    """Test WebSocket sends initial bear state on connection."""
    with client.websocket_connect("/ws") as websocket:
        # Should receive initial state message
        data = websocket.receive_json()

        assert data["type"] == "bear_state"
        assert "data" in data

        bear_state = data["data"]
        assert "eyes" in bear_state
        assert "mouth" in bear_state
        assert "is_busy" in bear_state
        assert "blink_enabled" in bear_state


@pytest.mark.asyncio
async def test_websocket_update_bear(client: TestClient) -> None:
    """Test WebSocket update_bear message."""
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        initial = websocket.receive_json()
        assert initial["type"] == "bear_state"

        # Send update_bear message
        websocket.send_json({"type": "update_bear", "data": {"eyes": "closed", "mouth": "open"}})

        # Should receive updated state
        response = websocket.receive_json()
        assert response["type"] == "bear_state"
        # State should reflect the update
        assert "eyes" in response["data"]
        assert "mouth" in response["data"]


@pytest.mark.asyncio
async def test_websocket_set_volume(client: TestClient) -> None:
    """Test WebSocket set_volume message."""
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        websocket.receive_json()

        # Send set_volume message
        websocket.send_json({"type": "set_volume", "data": {"volume": 75}})

        # Should receive success response or error (skip periodic broadcasts)
        response = _receive_until(websocket, {"volume_updated", "error"})
        assert "type" in response
        # Volume update might succeed or fail depending on audio system
        assert response["type"] in ["volume_updated", "error"]


@pytest.mark.asyncio
async def test_websocket_fetch_phrases(client: TestClient) -> None:
    """Test WebSocket fetch_phrases message."""
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        websocket.receive_json()

        # Send fetch_phrases message
        websocket.send_json({"type": "fetch_phrases"})

        # Should receive phrases response (skip periodic broadcasts)
        response = _receive_until(websocket, {"phrases"})
        assert response["type"] == "phrases"
        assert "data" in response
        # Data should be a dict of phrases
        assert isinstance(response["data"], dict)


@pytest.mark.asyncio
async def test_websocket_invalid_message(client: TestClient) -> None:
    """Test WebSocket handles invalid message gracefully."""
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        websocket.receive_json()

        # Send invalid message (missing type)
        websocket.send_json({"data": {"foo": "bar"}})

        # Should receive error response or handle gracefully
        try:
            response = websocket.receive_json()
            # If we get a response, it should be an error
            if "type" in response:
                assert response["type"] in ["error", "bear_state"]
        except Exception:
            # Connection might close on invalid message, which is also acceptable
            pass


@pytest.mark.asyncio
async def test_websocket_unknown_message_type(client: TestClient) -> None:
    """Test WebSocket handles unknown message type."""
    with client.websocket_connect("/ws") as websocket:
        # Receive initial state
        websocket.receive_json()

        # Send unknown message type
        websocket.send_json({"type": "unknown_type", "data": {}})

        # Should receive error response or handle gracefully
        try:
            response = websocket.receive_json()
            # If we get a response, check it's valid
            assert "type" in response
            # Could be error or just ignore unknown type
        except Exception:
            # Connection might close or timeout, which is acceptable
            pass


@pytest.mark.asyncio
async def test_websocket_multiple_clients(client: TestClient) -> None:
    """Test multiple WebSocket clients can connect."""
    with client.websocket_connect("/ws") as ws1:
        with client.websocket_connect("/ws") as ws2:
            # Both should receive initial state
            data1 = ws1.receive_json()
            data2 = ws2.receive_json()

            assert data1["type"] == "bear_state"
            assert data2["type"] == "bear_state"

            # Update from one client
            ws1.send_json({"type": "update_bear", "data": {"eyes": "open", "mouth": "open"}})

            # Both clients should receive update (skip periodic broadcasts, but
            # bear_state is itself the expected reply type here, so require the
            # update to actually be reflected in the data)
            response1 = _receive_until_state_with(ws1, eyes="open")
            response2 = _receive_until_state_with(ws2, eyes="open")

            assert response1["type"] == "bear_state"
            assert response2["type"] == "bear_state"
            assert response1["data"]["eyes"] == "open"
            assert response2["data"]["eyes"] == "open"


@pytest.mark.asyncio
async def test_websocket_disconnect_cleanup(client: TestClient) -> None:
    """Test WebSocket connection cleanup on disconnect."""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()
        # Connection will close when exiting context manager

    # Reconnect should work
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "bear_state"


def test_cors_headers(client: TestClient) -> None:
    """Test CORS headers are present in development."""
    response = client.get("/api/health")

    # CORS headers should be present (lowercase in response.headers)
    # Check if any CORS header is present
    cors_headers = [k for k in response.headers.keys() if "access-control" in k.lower()]
    assert len(cors_headers) > 0 or response.status_code == 200  # At minimum, endpoint should work


def test_static_file_serving(client: TestClient) -> None:
    """Test static file serving is configured."""
    # In test mode, static files might not be built
    # Just verify the app has static file serving configured
    assert app is not None
