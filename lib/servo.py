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
    self.open = None
    self.label = label

    # designate pins as OUT
    GPIO.setup(self.pwm_pin, GPIO.OUT)
    GPIO.setup(self.dir_pin, GPIO.OUT)
    GPIO.setup(self.cdir_pin, GPIO.OUT)

    self.pwm = GPIO.PWM(pwm_pin, 1)

  def move(self, opening=True, duration=.5):
    print("opened %s: %s (pwm=%s, dir=%s, cdir=%s)" % (self.label, opening, self.pwm_pin, self.dir_pin, self.cdir_pin))
    if(opening and (self.open == None or not self.open)):
      GPIO.output( self.dir_pin, GPIO.HIGH )
      GPIO.output( self.cdir_pin, GPIO.LOW )
    else:
      GPIO.output( self.dir_pin, GPIO.LOW )
      GPIO.output( self.cdir_pin, GPIO.HIGH )

    self.pwm.start(100)
    if(duration!=None):
      time.sleep(duration)
      self.stop()

    self.open = opening

  def stop(self):
    self.pwm.stop()
