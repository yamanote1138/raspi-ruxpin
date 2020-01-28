#!/usr/bin/env python
import time

class Servo:
  
  def __init__(self, pwm_pin=None, dir_pin=None, cdir_pin=None, pwm_freq=2000, duration=.5, speed=100, label="unknown"):

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
    self.speed = speed
    self.duration = duration

  def __del__(self):
    print("deleted servo instance '{}'").format(self.label)

  def __setDirection(self, direction="fwd"):
    self.direction = direction
    print("direction set to {}").format(direction)

  # set duration to 0 for continuous movement
  def __move(self, autoStop):
    # ensure all settings are appropriate to prevent unexpected behaivor
    if(self.direction == None): raise Exception('servo direction not set')
    if(self.duration is None): raise Exception('servo move duration not set')
    if(self.duration > 2): raise Exception('servo duration too long')

    print("{} motor started at speed {}").format(self.label, self.speed)

    if(autoStop):
      time.sleep(self.duration)
      self.stop()

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
    print("motor {} stopped").format(self.label)
