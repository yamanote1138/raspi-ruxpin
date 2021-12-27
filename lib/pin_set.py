from dataclasses import dataclass

@dataclass
class PinSet:
  """
    Class for storing motor pin settings

    Args:
      pwm (int): GPIO pin number to control motor pwm
      dir (int): GPIO pin number to control forward motion
      cdir (int): GPIO pin number to control reverse motion
  """
  pwm: int
  dir: int
  cdir: int
