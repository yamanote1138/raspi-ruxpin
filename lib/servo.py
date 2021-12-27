import logging
from time import sleep
from lib.pin_set import PinSet
from lib.direction import Direction
from lib.state import State

try:
  # checks if you have access to RPi.GPIO, which is available inside RPi
  import RPi.GPIO as GPIO
except:
  # In case of exception, you are executing your script outside of RPi, so import Mock.GPIO
  import Mock.GPIO as GPIO

class Servo:
  """
    Class for controlling a basic DC motor servo via GPIO

    Attributes:
      state State: motor position
      int speed: how fast to move the servo
      label str: arbitrary motor name, mostly used in logging. Defaults to "unknown".
  """

  def __init__(self, pins:PinSet, pwm_frequency:int=100, duration:float=.5, speed:int=100, label:str="unknown"):
    """
      Args:
        pins (PinSet, required): PinSet containing GPIO pin assignments
        pwm_frequency (int, optional): PWM frequency. Defaults to 100.
        duration (float, optional): how long the servo will move. Defaults to .5.
        speed (int, optional): how fast to move the servo. Defaults to 100.
        label (str, optional): arbitrary motor name, mostly used in logging. Defaults to "unknown".
    """

    # mute annoying 'This channel is already in use' warnings
    GPIO.setwarnings(False)

    # use Broadcom pin designations
    GPIO.setmode(GPIO.BCM)

    # set attribute values from arguments
    self.__pins = pins
    self.__duration = duration
    self.speed = speed
    self.label = label

    # validate duration
    if self.__duration <= 0:
      raise Exception("servo duration must be greater than 0")
    if self.__duration > 2:
      raise Exception("servo duration must be less than or equal to 2.0")


    # set initial state
    self.state = State.UNKNOWN

    # designate pins as OUT
    GPIO.setup(self.__pins.pwm, GPIO.OUT)
    GPIO.setup(self.__pins.dir, GPIO.OUT)
    GPIO.setup(self.__pins.cdir, GPIO.OUT)

    # initialize PWM
    self.pwm = GPIO.PWM(self.__pins.pwm, pwm_frequency)

    logging.debug("servo '%s' initialized", self.label)

  def __del__(self):
    self.pwm.stop()
    GPIO.cleanup()
    logging.debug("servo '%s' deleted", self.label)

  def __move(self):
    """move the servo"""

    # stop any current movement
    self.pwm.stop()

    self.pwm.start(self.speed)
    sleep(self.__duration)
    self.pwm.stop()

  def open(self):
    """open the servo; uses duration specified in config to determine when to stop"""
    self.stop()
    self.set_direction(Direction.OPENING)
    self.__move()
    self.state = State.OPEN
    logging.debug("servo '%s' opened", self.label)

  def close(self):
    """open the servo; uses duration specified in config to determine when to stop"""
    self.stop()
    self.set_direction(Direction.CLOSING)
    self.__move()
    self.state = State.CLOSED
    logging.debug("servo '%s' closed", self.label)

  def set_direction(self, direction:Direction):
    """ sets GPIO pins to the appropriate values based on specified direction

    Args:
        direction (Direction, required): specify in which direction to move the motor
    """
    if direction is Direction.OPENING:
      GPIO.output(self.__pins.dir, GPIO.HIGH)
      GPIO.output(self.__pins.cdir, GPIO.LOW)
    elif direction is Direction.CLOSING:
      GPIO.output(self.__pins.dir, GPIO.LOW)
      GPIO.output(self.__pins.cdir, GPIO.HIGH)
    elif direction is Direction.BRAKE:
      GPIO.output(self.__pins.dir, GPIO.LOW)
      GPIO.output(self.__pins.cdir, GPIO.LOW)
    else:
      raise Exception("unsupported servo direction")


  def stop(self):
    """set motor to brake and cease PWM signal"""
    self.set_direction(Direction.BRAKE)
    self.pwm.stop()
