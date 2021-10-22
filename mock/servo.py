#!/usr/bin/env python
import logging
from logging import raiseExceptions
from time import sleep

class Servo:
  
  def __init__(self, pwm_pin=None, dir_pin=None, cdir_pin=None, pwm_freq=100, duration=.5, speed=100, label="unknown"):

    # validate parameters
    if(pwm_pin is None): raise Exception("pwm pin not set")
    if(dir_pin is None): raise Exception("dir pin not set")
    if(cdir_pin is None): raise Exception("cdir pin not set")

    # set pin values for later use
    self.pwm_pin = pwm_pin
    self.dir_pin = dir_pin
    self.cdir_pin = cdir_pin

    # set initial state
    self.label = label
    self.state = ''
    self.speed = speed
    self.duration = duration

    logging.debug("servo \"{}\" initialized".format(self.label))

  def __del__(self):
    logging.debug("servo \"{}\" deleted".format(self.label))

  def __move(self, duration=None):
    # check for duration override, else use configured val
    if duration is None: duration = self.duration

    # ensure all settings are appropriate to prevent unexpected behaivor
    if(duration is None): raise Exception('servo move duration not set')
    if(duration > 2): raise Exception('servo duration too long')

    sleep(duration)

  def open(self, duration=None):
    self.stop()
    self.setDirection('opening')
    self.__move(duration)
    self.state = 'open'
    logging.debug("{} servo opened".format(self.label))

  def close(self, duration=None):
    self.stop()
    self.setDirection('closing')
    self.__move(duration)
    self.state = 'closed'
    logging.debug("{} servo closed".format(self.label))

  def setDirection(self, direction):
    if direction is None: raise Exception('direction not specified')
    if direction not in ['opening', 'closing', 'brake']: raise Exception('unsupported direction')

  def stop(self):
    self.setDirection('brake')
    logging.debug("{} servo stopped".format(self.label))
