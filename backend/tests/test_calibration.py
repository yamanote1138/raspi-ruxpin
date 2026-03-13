"""Tests for jaw calibration module."""

import json
from pathlib import Path

import pytest

from backend.core.enums import MouthPosition
from backend.hardware.calibration import (
    DEFAULT_CALIBRATION,
    POSITION_ORDER,
    get_default_calibration,
    interpolate_positions,
    load_calibration,
)


@pytest.mark.unit
def test_default_calibration_complete() -> None:
    """Default calibration should have all 7 positions."""
    table = get_default_calibration()
    assert len(table.positions) == 7
    for pos in MouthPosition:
        assert pos in table.positions


@pytest.mark.unit
def test_default_calibration_values() -> None:
    """Default values should match the hardcoded defaults."""
    table = get_default_calibration()
    for pos in MouthPosition:
        upper, lower = table.get_angles(pos)
        assert upper == DEFAULT_CALIBRATION[pos.value]["upper"]
        assert lower == DEFAULT_CALIBRATION[pos.value]["lower"]


@pytest.mark.unit
def test_default_calibration_monotonic() -> None:
    """Calibration angles should decrease from C (closed) to W (wide open)."""
    table = get_default_calibration()
    prev_upper = 999
    for pos in POSITION_ORDER:
        upper, lower = table.get_angles(pos)
        assert upper <= prev_upper, f"Position {pos}: upper {upper} > prev {prev_upper}"
        prev_upper = upper


@pytest.mark.unit
def test_load_calibration(tmp_path: Path) -> None:
    """Test loading calibration from JSON file."""
    cal_data = {
        "C": {"upper": 100, "lower": 98},
        "T": {"upper": 95, "lower": 93},
        "S": {"upper": 90, "lower": 88},
        "N": {"upper": 85, "lower": 83},
        "M": {"upper": 75, "lower": 73},
        "L": {"upper": 65, "lower": 63},
        "W": {"upper": 50, "lower": 48},
    }
    cal_file = tmp_path / "test_cal.json"
    cal_file.write_text(json.dumps(cal_data))

    table = load_calibration(cal_file)
    assert len(table.positions) == 7
    upper, lower = table.get_angles(MouthPosition.C)
    assert upper == 100
    assert lower == 98


@pytest.mark.unit
def test_load_calibration_missing_positions(tmp_path: Path) -> None:
    """Missing positions should use defaults."""
    cal_data = {
        "C": {"upper": 100, "lower": 98},
        "W": {"upper": 50, "lower": 48},
    }
    cal_file = tmp_path / "partial_cal.json"
    cal_file.write_text(json.dumps(cal_data))

    table = load_calibration(cal_file)
    assert len(table.positions) == 7

    # C should use file values
    upper, lower = table.get_angles(MouthPosition.C)
    assert upper == 100

    # T should use defaults (missing from file)
    upper, lower = table.get_angles(MouthPosition.T)
    assert upper == DEFAULT_CALIBRATION["T"]["upper"]


@pytest.mark.unit
def test_interpolate_positions() -> None:
    """Interpolation from closed + wide should produce 7 positions."""
    table = interpolate_positions(
        closed_upper=100, closed_lower=98,
        wide_upper=40, wide_lower=38,
    )
    assert len(table.positions) == 7

    # First (C) should match closed
    c_upper, c_lower = table.get_angles(MouthPosition.C)
    assert c_upper == 100
    assert c_lower == 98

    # Last (W) should match wide
    w_upper, w_lower = table.get_angles(MouthPosition.W)
    assert w_upper == 40
    assert w_lower == 38


@pytest.mark.unit
def test_interpolate_is_monotonic() -> None:
    """Interpolated values should decrease monotonically from C to W."""
    table = interpolate_positions(100, 98, 40, 38)
    prev_upper = 999
    for pos in POSITION_ORDER:
        upper, _ = table.get_angles(pos)
        assert upper <= prev_upper
        prev_upper = upper


@pytest.mark.unit
def test_calibration_to_dict() -> None:
    """Test serialization to dict."""
    table = get_default_calibration()
    d = table.to_dict()
    assert "C" in d
    assert "W" in d
    assert d["C"]["upper"] == DEFAULT_CALIBRATION["C"]["upper"]


@pytest.mark.unit
def test_position_order() -> None:
    """POSITION_ORDER should contain all 7 positions in order."""
    assert len(POSITION_ORDER) == 7
    assert POSITION_ORDER[0] == MouthPosition.C
    assert POSITION_ORDER[-1] == MouthPosition.W
