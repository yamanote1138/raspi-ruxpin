#!/usr/bin/env python
import RPi.GPIO as GPIO
#import subprocess
import time

class Servo:
  
  def __init__(self, pwm_pin, dir_pin, cdir_pin, label="unknown"):
    # map configured pins to variables
    self.pwm_pin = pwm_pin
    self.dir_pin = dir_pin
    self.cdir_pin = cdir_pin
    self.is_open = None
    self.label = label
    self.direction = "fwd"

    # designate pins as OUT
    GPIO.setup(self.pwm_pin, GPIO.OUT)
    GPIO.setup(self.dir_pin, GPIO.OUT)
    GPIO.setup(self.cdir_pin, GPIO.OUT)

    self.pwm = GPIO.PWM(pwm_pin, 2000)

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
  def __move(self, duration=.5):
    # ensure all settings are appropriate to prevent unexpected behaivor
    if(self.direction == None): raise Exception('servo direction not set')
    if(duration is None): raise Exception('servo move duration not set')
    if(duration > 5): raise Exception('servo duration too long')

    self.pwm.start(100)

    if(duration is not None and duration > 0):
      time.sleep(duration)
      self.pwm.stop()

  def open(self, duration=0):
    self.__setDirection("fwd")
    self.__move(duration)

  def close(self, duration=0):
    self.__setDirection("rev")
    self.__move(duration)

  def blink(self):
    self.open(.4)
    time.sleep(.5)
    self.close(.4)

  def stop(self):
    self.pwm.stop()
