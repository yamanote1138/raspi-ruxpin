#!/usr/bin/env python
import RPi.GPIO as GPIO
#import subprocess
import time

class Servo:
  
  def __init__(self, pwm_pin=None, dir_pin=None, cdir_pin=None, pwm_freq=2000, duration=.5, label="unknown"):

    # validate parameters
    if(pwm_pin is None): raise Exception("pwm pin not set")
    if(dir_pin is None): raise Exception("dir pin not set")
    if(cdir_pin is None): raise Exception("cdir pin not set")

    # set pin values for later use
    self.pwm_pin = pwm_pin
    self.dir_pin = dir_pin
    self.cdir_pin = cdir_pin

    # set initial state
    self.is_open = None
    self.label = label
    self.direction = "fwd"
    self.duration = duration

    # designate pins as OUT
    GPIO.setup(self.pwm_pin, GPIO.OUT)
    GPIO.setup(self.dir_pin, GPIO.OUT)
    GPIO.setup(self.cdir_pin, GPIO.OUT)

    # initialize PWM
    self.pwm = GPIO.PWM(self.pwm_pin, pwm_freq)

  def __del__(self):
    self.pwm.stop()

  def __setDirection(self, direction="fwd"):
    self.direction = direction
    if(direction == "fwd"):
      GPIO.output( self.dir_pin, GPIO.HIGH )
      GPIO.output( self.cdir_pin, GPIO.LOW )
    elif(direction == "rev"):
      GPIO.output( self.dir_pin, GPIO.LOW )
      GPIO.output( self.cdir_pin, GPIO.HIGH )
    else:
      raise Exception("unsupported motor direction: %s", (self.direction))

  # set duration to 0 for continuous movement
  def __move(self, autoStop):
    # ensure all settings are appropriate to prevent unexpected behaivor
    if(self.direction == None): raise Exception('servo direction not set')
    if(self.duration is None): raise Exception('servo move duration not set')
    if(self.duration > 2): raise Exception('servo duration too long')

    self.pwm.start(100)

    if(autoStop):
      time.sleep(self.duration)
      self.pwm.stop()

  def open(self, autoStop=True):
    self.__setDirection("fwd")
    self.__move(autoStop)

  def close(self, autoStop=True):
    self.__setDirection("rev")
    self.__move(autoStop)

  def blink(self):
    self.open()
    time.sleep(.5)
    self.close()

  def stop(self):
    self.pwm.stop()
