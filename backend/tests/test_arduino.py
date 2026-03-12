"""Tests for Arduino serial communication."""


import pytest

from backend.core.enums import MouthPosition, ServoType, SyncMode
from backend.core.exceptions import SerialError
from backend.hardware.arduino import ArduinoController
from backend.hardware.calibration import get_default_calibration


@pytest.fixture
def controller():
    """Provide a mock-mode Arduino controller."""
    return ArduinoController(
        port="/dev/mock",
        baud_rate=115200,
        timeout=1.0,
        connect_timeout=5.0,
        use_mock=True,
    )


@pytest.mark.unit
async def test_connect_with_mock(controller):
    """Test connection with mock serial."""
    await controller.connect()
    assert controller.connected is True
    await controller.disconnect()
    assert controller.connected is False


@pytest.mark.unit
async def test_connect_sends_config(controller):
    """Test that connect sends servo type, calibration, and mode."""
    calibration = get_default_calibration()
    await controller.connect(
        servo_type=ServoType.HBRIDGE,
        calibration=calibration,
        sync_mode=SyncMode.AMPLITUDE,
    )
    assert controller.connected is True
    await controller.disconnect()


@pytest.mark.unit
async def test_mouth_position_command(controller):
    """Test sending mouth position commands."""
    await controller.connect()
    await controller.set_mouth_position(MouthPosition.W)
    await controller.set_mouth_position(MouthPosition.C)
    await controller.disconnect()


@pytest.mark.unit
async def test_mouth_angles_command(controller):
    """Test sending direct jaw angle commands."""
    await controller.connect()
    await controller.set_mouth_angles(90, 85)
    await controller.disconnect()


@pytest.mark.unit
async def test_eyes_commands(controller):
    """Test eye control commands."""
    await controller.connect()
    await controller.open_eyes()
    await controller.close_eyes()
    await controller.blink_eyes()
    await controller.disconnect()


@pytest.mark.unit
async def test_mode_switch(controller):
    """Test switching sync mode."""
    await controller.connect()
    await controller.set_mode(SyncMode.PHONEME)
    await controller.set_mode(SyncMode.AMPLITUDE)
    await controller.disconnect()


@pytest.mark.unit
async def test_ping(controller):
    """Test ping/pong health check."""
    await controller.connect()
    result = await controller.ping()
    assert result is True
    await controller.disconnect()


@pytest.mark.unit
async def test_send_command_when_disconnected():
    """Test that sending commands when disconnected raises error."""
    controller = ArduinoController(use_mock=True)
    with pytest.raises(SerialError, match="Not connected"):
        await controller.set_mouth_position(MouthPosition.C)


@pytest.mark.unit
async def test_status_parsing():
    """Test parsing of STATUS response lines."""
    status = ArduinoController._parse_status("STATUS:MODE:AMPLITUDE,MOUTH:C,EYES:open")
    assert status.mode == SyncMode.AMPLITUDE
    assert status.mouth_position == MouthPosition.C
    assert status.eyes_open is True


@pytest.mark.unit
async def test_status_parsing_phoneme_closed():
    """Test parsing STATUS with phoneme mode and closed eyes."""
    status = ArduinoController._parse_status("STATUS:MODE:PHONEME,MOUTH:W,EYES:closed")
    assert status.mode == SyncMode.PHONEME
    assert status.mouth_position == MouthPosition.W
    assert status.eyes_open is False


@pytest.mark.unit
async def test_status_parsing_invalid():
    """Test parsing invalid STATUS response."""
    with pytest.raises(SerialError, match="Failed to parse"):
        ArduinoController._parse_status("STATUS:COMPLETELY_INVALID_NO_COMMAS")
