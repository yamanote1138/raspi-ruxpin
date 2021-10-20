#!/usr/bin/env python
from logging import raiseExceptions
import RPi.GPIO as GPIO
import time

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
    self.to = ''
    self.state = ''
    self.speed = speed
    self.duration = duration

    # designate pins as OUT
    GPIO.setup(self.pwm_pin, GPIO.OUT)
    GPIO.setup(self.dir_pin, GPIO.OUT)
    GPIO.setup(self.cdir_pin, GPIO.OUT)

    # initialize PWM
    self.pwm = GPIO.PWM(self.pwm_pin, pwm_freq)

    print("servo \"{}\" initialized".format(self.label))

  def __del__(self):
    self.pwm.stop()
    GPIO.cleanup()
    print("servo \"{}\" deleted".format(self.label))

  def __move(self, duration=None):
    # stop any current movement
    self.pwm.stop()

    # check for duration override, else use configured val
    if duration is None: duration = self.duration

    # ensure all settings are appropriate to prevent unexpected behaivor
    if(duration is None): raise Exception('servo move duration not set')
    if(duration > 2): raise Exception('servo duration too long')

    self.pwm.start(self.speed)
    time.sleep(duration)
    self.pwm.stop()

  def open(self, duration=None):
    self.stop()
    self.setDirection('open')
    self.__move(duration)
    self.state = 'open'
    self.to = ''
    print("{} servo opened".format(self.label))

  def close(self, duration=None):
    self.stop()
    self.setDirection('closed')
    self.__move(duration)
    self.state = 'closed'
    self.to = ''
    print("{} servo closed".format(self.label))

  def setDirection(self, direction):
    if direction is None: raise Exception('direction not specified')
    if direction not in ['open', 'closed', 'stall']: raise Exception('unsupported direction')

    if direction == 'open':
      GPIO.output( self.dir_pin, GPIO.HIGH )
      GPIO.output( self.cdir_pin, GPIO.LOW )
    elif direction == 'closed':
      GPIO.output( self.dir_pin, GPIO.LOW )
      GPIO.output( self.cdir_pin, GPIO.HIGH )
    else:
      GPIO.output( self.dir_pin, GPIO.LOW )
      GPIO.output( self.cdir_pin, GPIO.LOW )



  def stop(self):
    self.pwm.stop()
