#!/usr/bin/env python
import logging

from time import sleep
from threading import Thread
from mock.servo import Servo

class Bear:
  def __init__(self, config):
    self.isRunning = False
    self.isTalking = False

    # add list of supported phrases
    self.phrases = config.phrases

    # bind mouth and eye servos based on pins defined in config
    self.eyes = Servo(
      pwm_pin=config.getint('pins', 'pwma'),
      dir_pin=config.getint('pins', 'ain1'),
      cdir_pin=config.getint('pins', 'ain2'),
      duration=config.getfloat('settings', 'eyes_duration'),
      speed=config.getint('settings', 'eyes_speed'),
      label='eyes'
    )

    self.mouth = Servo(
      pwm_pin=config.getint('pins', 'pwmb'),
      dir_pin=config.getint('pins', 'bin1'),
      cdir_pin=config.getint('pins', 'bin2'),
      duration=config.getfloat('settings', 'mouth_duration'),
      speed=config.getint('settings', 'mouth_speed'),
      label='mouth'
    )

    self.character = {
      'name': config.get('character', 'name'),
      'prefix': config.get('character', 'prefix')
    }
    logging.debug('character is:{}\nprefix is:{}'.format(self.character['name'], self.character['prefix']))

    #set starting motor positions
    self.eyes.open()
    self.mouth.close()
    self.talkThread = Thread(target=self.__talkMonitor)
    logging.debug("bear constructor finished")

  def __del__(self):
    logging.debug("bear deconstructor finished")

  def activate(self):
    self.isRunning = True
    self.talkThread.start()
    logging.debug("bear instance activated")

  def deactivate(self):
    self.isRunning = False
    self.isTalking = False
    logging.debug("bear instance deactivated")

  def __talkMonitor(self):
    sleep(.1)

  def update(self, data):
    if self.isTalking:
      logging.error('cannot update bear while it is talking')
    else:
      if 'eyes' in data:
        if data['eyes'] == 'open' and self.eyes.state != 'open': self.eyes.open()
        elif data['eyes'] == 'closed' and self.eyes.state != 'closed': self.eyes.close()
      if 'mouth' in data:
        if data['mouth'] == 'open' and self.mouth.state != 'open': self.mouth.open()
        elif data['mouth'] == 'closed' and self.mouth.state != 'closed': self.mouth.close()

      logging.debug("updated bear")
      logging.debug(data)
      sleep(1)

  def play(self, filename):
   logging.debug('playing: "{}"'.format(filename))   
   sleep(2)

  def say(self, text):
   logging.debug('saying: "{}"'.format(text))
   self.play("espeak")
