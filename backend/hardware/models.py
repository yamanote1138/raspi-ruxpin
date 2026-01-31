"""Hardware models and data structures."""

from pydantic import BaseModel, Field


class PinSet(BaseModel):
    """Represents a set of GPIO pins for a servo motor."""

    pwm: int = Field(..., ge=0, le=27, description="PWM control pin (BCM numbering)")
    dir: int = Field(..., ge=0, le=27, description="Direction control pin")
    cdir: int = Field(..., ge=0, le=27, description="Counter-direction control pin")

    def __hash__(self) -> int:
        """Make PinSet hashable for use in sets/dicts."""
        return hash((self.pwm, self.dir, self.cdir))


class ServoConfig(BaseModel):
    """Configuration for a single servo motor."""

    pins: PinSet = Field(..., description="GPIO pins for this servo")
    speed: int = Field(default=100, ge=1, le=1000, description="PWM frequency in Hz")
    duration: float = Field(default=0.4, gt=0, le=2.0, description="Default movement duration")

    class Config:
        frozen = True
