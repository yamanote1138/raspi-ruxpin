#!/usr/bin/env python
from logging import raiseExceptions
from time import sleep
import logging

try:
  # checks if you have access to RPi.GPIO, which is available inside RPi
  import RPi.GPIO as GPIO
except:
  # In case of exception, you are executing your script outside of RPi, so import Mock.GPIO
  import Mock.GPIO as GPIO

class Servo:
  
  def __init__(self, pwm_pin=None, dir_pin=None, cdir_pin=None, pwm_freq=100, duration=.5, speed=100, label="unknown"):

    # mute annoying 'This channel is already in use' warnings
    GPIO.setwarnings(False)

    # validate parameters
    if(pwm_pin is None): raise Exception("pwm pin not set")
    if(dir_pin is None): raise Exception("dir pin not set")
    if(cdir_pin is None): raise Exception("cdir pin not set")

    # use Broadcom pin designations
    GPIO.setmode(GPIO.BCM)

    # set pin values for later use
    self.pwm_pin = pwm_pin
    self.dir_pin = dir_pin
    self.cdir_pin = cdir_pin

    # set initial state
    self.label = label
    self.state = ''
    self.speed = speed
    self.duration = duration

    # designate pins as OUT
    GPIO.setup(self.pwm_pin, GPIO.OUT)
    GPIO.setup(self.dir_pin, GPIO.OUT)
    GPIO.setup(self.cdir_pin, GPIO.OUT)

    # initialize PWM
    self.pwm = GPIO.PWM(self.pwm_pin, pwm_freq)

    logging.debug(f"servo '{self.label}' initialized")

  def __del__(self):
    self.pwm.stop()
    GPIO.cleanup()
    logging.debug(f"servo '{self.label}' deleted")

  def __move(self, duration=None):
    # stop any current movement
    self.pwm.stop()

    # check for duration override, else use configured val
    if duration is None: duration = self.duration

    # ensure all settings are appropriate to prevent unexpected behaivor
    if(duration is None): raise Exception('servo move duration not set')
    if(duration > 2): raise Exception('servo duration too long')

    self.pwm.start(self.speed)
    sleep(duration)
    self.pwm.stop()

  def open(self, duration=None):
    self.stop()
    self.setDirection('opening')
    self.__move(duration)
    self.state = 'open'
    logging.debug(f"servo '{self.label}' opened")

  def close(self, duration=None):
    self.stop()
    self.setDirection('closing')
    self.__move(duration)
    self.state = 'closed'
    logging.debug(f"servo '{self.label}' closed")

  def setDirection(self, direction):
    if direction is None: raise Exception('direction not specified')
    if direction not in ['opening', 'closing', 'brake']: raise Exception('unsupported direction')

    if direction == 'opening':
      GPIO.output( self.dir_pin, GPIO.HIGH )
      GPIO.output( self.cdir_pin, GPIO.LOW )
    elif direction == 'closing':
      GPIO.output( self.dir_pin, GPIO.LOW )
      GPIO.output( self.cdir_pin, GPIO.HIGH )
    else:
      GPIO.output( self.dir_pin, GPIO.LOW )
      GPIO.output( self.cdir_pin, GPIO.LOW )

  def stop(self):
    self.setDirection('brake')
    self.pwm.stop()
