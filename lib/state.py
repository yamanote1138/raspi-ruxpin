from enum import Enum

class State(Enum):
  """enum class to define possible motor states

  Args:
      Enum ([type]): [description]
  """
  OPEN = True
  CLOSED = False
  UNKNOWN = None
