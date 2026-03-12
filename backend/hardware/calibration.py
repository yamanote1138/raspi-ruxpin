"""Jaw calibration data for 7-position mouth model.

Manages calibration tables that map each MouthPosition to upper and lower
servo angles. Supports loading from JSON, interpolation from just two
reference positions (closed + wide), and default values.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from backend.core.enums import MouthPosition

logger = logging.getLogger(__name__)

# Default calibration values (from hardware testing with original Teddy Ruxpin servos)
DEFAULT_CALIBRATION: dict[str, dict[str, int]] = {
    "C": {"upper": 101, "lower": 99},
    "T": {"upper": 97, "lower": 95},
    "S": {"upper": 92, "lower": 90},
    "N": {"upper": 86, "lower": 84},
    "M": {"upper": 78, "lower": 76},
    "L": {"upper": 68, "lower": 66},
    "W": {"upper": 55, "lower": 53},
}

# Ordered positions from closed to wide
POSITION_ORDER: list[MouthPosition] = [
    MouthPosition.C,
    MouthPosition.T,
    MouthPosition.S,
    MouthPosition.N,
    MouthPosition.M,
    MouthPosition.L,
    MouthPosition.W,
]


@dataclass
class PositionAngles:
    """Servo angles for a single mouth position."""

    upper: int
    lower: int


@dataclass
class CalibrationTable:
    """Complete calibration table for all 7 mouth positions."""

    positions: dict[MouthPosition, PositionAngles] = field(default_factory=dict)

    def get_angles(self, position: MouthPosition) -> tuple[int, int]:
        """Get servo angles for a mouth position.

        Args:
            position: The mouth position to look up.

        Returns:
            Tuple of (upper_angle, lower_angle).
        """
        angles = self.positions[position]
        return angles.upper, angles.lower

    def to_dict(self) -> dict[str, dict[str, int]]:
        """Serialize to dictionary."""
        return {
            pos.value: {"upper": angles.upper, "lower": angles.lower}
            for pos, angles in self.positions.items()
        }


def load_calibration(path: Path) -> CalibrationTable:
    """Load calibration data from a JSON file.

    Args:
        path: Path to calibration JSON file.

    Returns:
        Populated CalibrationTable.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    table = CalibrationTable()
    for pos in MouthPosition:
        if pos.value in data:
            entry = data[pos.value]
            table.positions[pos] = PositionAngles(upper=entry["upper"], lower=entry["lower"])
        else:
            logger.warning(f"Missing calibration for position {pos.value}, using defaults")
            defaults = DEFAULT_CALIBRATION[pos.value]
            table.positions[pos] = PositionAngles(upper=defaults["upper"], lower=defaults["lower"])

    logger.info(f"Loaded calibration from {path}")
    return table


def get_default_calibration() -> CalibrationTable:
    """Get the default calibration table.

    Returns:
        CalibrationTable with default values.
    """
    table = CalibrationTable()
    for pos in MouthPosition:
        defaults = DEFAULT_CALIBRATION[pos.value]
        table.positions[pos] = PositionAngles(upper=defaults["upper"], lower=defaults["lower"])
    return table


def interpolate_positions(
    closed_upper: int,
    closed_lower: int,
    wide_upper: int,
    wide_lower: int,
) -> CalibrationTable:
    """Interpolate a full 7-position table from just closed and wide reference points.

    The 5 intermediate positions are evenly distributed between C (closed) and W (wide).

    Args:
        closed_upper: Upper servo angle for closed position.
        closed_lower: Lower servo angle for closed position.
        wide_upper: Upper servo angle for wide open position.
        wide_lower: Lower servo angle for wide open position.

    Returns:
        Fully interpolated CalibrationTable.
    """
    table = CalibrationTable()
    num_positions = len(POSITION_ORDER)

    for i, pos in enumerate(POSITION_ORDER):
        fraction = i / (num_positions - 1)
        upper = round(closed_upper + (wide_upper - closed_upper) * fraction)
        lower = round(closed_lower + (wide_lower - closed_lower) * fraction)
        table.positions[pos] = PositionAngles(upper=upper, lower=lower)

    return table


