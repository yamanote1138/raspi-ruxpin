from enum import Enum

class Direction(Enum):
  """enum class to define possible motor directions

  Args:
      Enum ([type]): [description]
  """
  OPENING = "opening"
  CLOSING = "closing"
  BRAKE = "brake"
