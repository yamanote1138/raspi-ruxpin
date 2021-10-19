#!/usr/bin/env python
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

  def __move(self):
    # ensure all settings are appropriate to prevent unexpected behaivor
    if(self.duration is None): raise Exception('servo move duration not set')
    if(self.duration > 2): raise Exception('servo duration too long')

    self.pwm.start(self.speed)
    time.sleep(self.duration)
    self.pwm.stop()

  def open(self):
    self.stop()
    GPIO.output( self.dir_pin, GPIO.HIGH )
    GPIO.output( self.cdir_pin, GPIO.LOW )
    self.__move()
    self.state = 'open'
    self.to = ''
    print("servo opened")

  def close(self):
    self.stop()
    GPIO.output( self.dir_pin, GPIO.LOW )
    GPIO.output( self.cdir_pin, GPIO.HIGH )
    self.__move()
    self.state = 'closed'
    self.to = ''
    print("servo closed")

  def stop(self):
    self.pwm.stop()
