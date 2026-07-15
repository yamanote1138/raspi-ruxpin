"""Tests for servo control."""

import pytest

from backend.core.enums import Direction, State
from backend.core.exceptions import ServoError
from backend.hardware.gpio_manager import GPIOManager
from backend.hardware.models import PinSet
from backend.hardware.servo import Servo


@pytest.fixture
def pin_set() -> PinSet:
    """Provide test pin configuration."""
    return PinSet(pwm=21, dir=16, cdir=20)


@pytest.fixture
async def servo(mock_gpio_manager: GPIOManager, pin_set: PinSet) -> Servo:
    """Provide test servo instance."""
    s = Servo(
        name="test_servo",
        pins=pin_set,
        speed=100,
        default_duration=0.4,
        gpio_manager=mock_gpio_manager,
    )
    await s.initialize()
    return s


@pytest.mark.asyncio
async def test_servo_initialization(mock_gpio_manager: GPIOManager, pin_set: PinSet) -> None:
    """Test servo initializes correctly."""
    servo = Servo(
        name="test_servo",
        pins=pin_set,
        speed=100,
        default_duration=0.4,
        gpio_manager=mock_gpio_manager,
    )

    assert servo.pins == pin_set
    assert servo.speed == 100
    assert servo.default_duration == 0.4
    assert servo.name == "test_servo"
    assert servo.state == State.UNKNOWN


@pytest.mark.asyncio
async def test_servo_open(servo: Servo) -> None:
    """Test servo open operation."""
    await servo.open()

    # Should set state to OPEN
    assert servo.state == State.OPEN


@pytest.mark.asyncio
async def test_servo_close(servo: Servo) -> None:
    """Test servo close operation."""
    await servo.close()

    # Should set state to CLOSED
    assert servo.state == State.CLOSED


@pytest.mark.asyncio
async def test_servo_brake(servo: Servo) -> None:
    """Test servo brake operation."""
    await servo._set_direction(Direction.BRAKE)

    # Should set brake direction
    # Just verify no exception was raised


@pytest.mark.asyncio
async def test_servo_duration_validation(mock_gpio_manager: GPIOManager) -> None:
    """Test servo duration validation."""
    pin_set = PinSet(pwm=21, dir=16, cdir=20)

    # Valid duration
    servo1 = Servo(
        name="test",
        pins=pin_set,
        speed=100,
        default_duration=0.5,
        gpio_manager=mock_gpio_manager,
    )
    assert servo1.default_duration == 0.5

    # Zero duration should be invalid
    with pytest.raises(ServoError, match="Duration must be between"):
        Servo(
            name="test",
            pins=pin_set,
            speed=100,
            default_duration=0.0,
            gpio_manager=mock_gpio_manager,
        )

    # Negative duration should be invalid
    with pytest.raises(ServoError, match="Duration must be between"):
        Servo(
            name="test",
            pins=pin_set,
            speed=100,
            default_duration=-0.1,
            gpio_manager=mock_gpio_manager,
        )

    # Duration too long should be invalid
    with pytest.raises(ServoError, match="Duration must be between"):
        Servo(
            name="test",
            pins=pin_set,
            speed=100,
            default_duration=3.0,
            gpio_manager=mock_gpio_manager,
        )


@pytest.mark.asyncio
async def test_servo_set_direction_opening(servo: Servo) -> None:
    """Test setting direction to OPENING."""
    await servo._set_direction(Direction.OPENING)

    # Just verify no exception was raised


@pytest.mark.asyncio
async def test_servo_set_direction_closing(servo: Servo) -> None:
    """Test setting direction to CLOSING."""
    await servo._set_direction(Direction.CLOSING)

    # Just verify no exception was raised


@pytest.mark.asyncio
async def test_servo_pwm_start(servo: Servo) -> None:
    """Test PWM starts during operation."""
    await servo.open()

    # PWM should be created and started
    assert servo.pwm is not None


@pytest.mark.asyncio
async def test_servo_speed_validation(mock_gpio_manager: GPIOManager) -> None:
    """Test servo speed validation."""
    pin_set = PinSet(pwm=21, dir=16, cdir=20)

    # Valid speed
    servo1 = Servo(
        name="test",
        pins=pin_set,
        speed=500,
        default_duration=0.4,
        gpio_manager=mock_gpio_manager,
    )
    assert servo1.speed == 500

    # Speed too low should be invalid
    with pytest.raises(ServoError, match="Speed must be between"):
        Servo(
            name="test",
            pins=pin_set,
            speed=0,
            default_duration=0.4,
            gpio_manager=mock_gpio_manager,
        )

    # Speed too high should be invalid
    with pytest.raises(ServoError, match="Speed must be between"):
        Servo(
            name="test",
            pins=pin_set,
            speed=1001,
            default_duration=0.4,
            gpio_manager=mock_gpio_manager,
        )


def test_pin_set_model() -> None:
    """Test PinSet Pydantic model."""
    pins = PinSet(pwm=21, dir=16, cdir=20)

    assert pins.pwm == 21
    assert pins.dir == 16
    assert pins.cdir == 20


def test_pin_set_validation() -> None:
    """Test PinSet validation."""
    # Valid pins
    pins = PinSet(pwm=21, dir=16, cdir=20)
    assert pins.pwm == 21

    # Invalid PWM (negative)
    with pytest.raises(ValueError):
        PinSet(pwm=-1, dir=16, cdir=20)
