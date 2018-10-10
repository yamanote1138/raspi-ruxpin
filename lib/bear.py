#!/usr/bin/env python
import time
import RPi.GPIO as GPIO

class Servo:
  def __init__(self, open_pin, close_pin):
    # map configured pins to variables
    self.open_pin = open_pin
    self.close_pin = close_pin
    # designate pins as OUT
    GPIO.setup(self.open_pin, GPIO.OUT)
    GPIO.setup(self.close_pin, GPIO.OUT)

  def open(self):
    GPIO.output( self.open_pin, GPIO.HIGH )
    GPIO.output( self.close_pin, GPIO.LOW )
    time.sleep(1)
    GPIO.output( self.open_pin, GPIO.LOW )
    GPIO.output( self.close_pin, GPIO.LOW )

  def close(self):
    GPIO.output( self.open_pin, GPIO.LOW )
    GPIO.output( self.close_pin, GPIO.HIGH )
    time.sleep(1)
    GPIO.output( self.open_pin, GPIO.LOW )
    GPIO.output( self.close_pin, GPIO.LOW )

class Bear:
  def __init__(self, config):
    # use Broadcom pin designations
    GPIO.setmode(GPIO.BCM)
    self.mouth = Servo(config.getint('pins', 'mouth_open'), config.getint('pins', 'mouth_closed'))
    self.eyes = Servo(config.getint('pins', 'eyes_open'), config.getint('pins', 'eyes_closed'))

  def __del__(self):
    GPIO.cleanup()
