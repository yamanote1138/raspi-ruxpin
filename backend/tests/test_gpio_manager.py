"""Tests for GPIO manager."""

import pytest
from unittest.mock import MagicMock, patch

from backend.hardware.gpio_manager import GPIOManager
from backend.core.exceptions import GPIOError


def test_gpio_manager_initialization_mock():
    """Test GPIO manager initializes with mock GPIO."""
    manager = GPIOManager(use_mock=True)

    assert manager.is_initialized is False
    assert manager.gpio is not None


def test_gpio_manager_initialize_mock():
    """Test GPIO manager initialize method with mock."""
    manager = GPIOManager(use_mock=True)
    manager.initialize()

    assert manager.is_initialized is True
    assert manager.gpio is not None


def test_gpio_manager_setup_pin(mock_gpio_manager):
    """Test setting up a GPIO pin."""
    mock_gpio_manager.setup_pin(21, "OUT")

    assert 21 in mock_gpio_manager.active_pins


def test_gpio_manager_output(mock_gpio_manager):
    """Test GPIO output."""
    # First setup the pin
    mock_gpio_manager.setup_pin(21, "OUT")

    # Then test output
    mock_gpio_manager.output(21, True)
    # Just verify no exception was raised


def test_gpio_manager_pwm_creation(mock_gpio_manager):
    """Test PWM creation."""
    # First setup the pin
    mock_gpio_manager.setup_pin(21, "OUT")

    # Create PWM
    pwm = mock_gpio_manager.create_pwm(21, 100)

    assert pwm is not None
    assert 21 in mock_gpio_manager.active_pwms


def test_gpio_manager_cleanup(mock_gpio_manager):
    """Test GPIO cleanup."""
    # Setup a pin first
    mock_gpio_manager.setup_pin(21, "OUT")

    # Cleanup all
    mock_gpio_manager.cleanup_all()

    assert mock_gpio_manager.is_initialized is False
    assert len(mock_gpio_manager.active_pins) == 0


def test_gpio_manager_cleanup_not_initialized():
    """Test cleanup when not initialized doesn't error."""
    manager = GPIOManager(use_mock=True)
    manager.cleanup_all()  # Should not raise


def test_gpio_manager_double_initialize(mock_gpio_manager):
    """Test double initialization is handled gracefully."""
    # Already initialized in fixture
    mock_gpio_manager.initialize()  # Should not error
    assert mock_gpio_manager.is_initialized is True


def test_gpio_manager_context_manager():
    """Test GPIO manager as context manager."""
    with GPIOManager(use_mock=True) as manager:
        manager.initialize()
        assert manager.is_initialized is True

    # Should cleanup on exit
    assert manager.is_initialized is False


def test_gpio_manager_output_low(mock_gpio_manager):
    """Test GPIO output low."""
    # First setup the pin
    mock_gpio_manager.setup_pin(25, "OUT")

    # Then test output
    mock_gpio_manager.output(25, False)
    # Just verify no exception was raised


def test_gpio_manager_setup_multiple_pins(mock_gpio_manager):
    """Test setting up multiple pins."""
    pins = [21, 16, 20, 25, 7, 8]

    for pin in pins:
        mock_gpio_manager.setup_pin(pin, "OUT")

    assert len(mock_gpio_manager.active_pins) == len(pins)


def test_gpio_manager_output_without_setup():
    """Test that output raises error if pin not set up."""
    manager = GPIOManager(use_mock=True)
    manager.initialize()

    with pytest.raises(GPIOError, match="Pin 21 not set up"):
        manager.output(21, True)


def test_gpio_manager_pwm_without_setup():
    """Test that PWM creation raises error if pin not set up."""
    manager = GPIOManager(use_mock=True)
    manager.initialize()

    with pytest.raises(GPIOError, match="Pin 21 not set up"):
        manager.create_pwm(21, 100)
