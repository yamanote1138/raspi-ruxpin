#!/usr/bin/env python
import logging, random, subprocess, time

from time import sleep
from threading import Thread

from lib.servo import Servo
from lib.audioPlayer import AudioPlayer

class Bear:
  def __init__(self, config):
    self.isRunning = True
    self.isTalking = False

    # attach audio player
    self.audio = AudioPlayer(config)

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
    logging.debug('character is:{}'.format(self.character['name']));
    logging.debug('prefix is:{}'.format(self.character['prefix']));

    self.talkThread = Thread(target=self.__talkMonitor, daemon=True)
    self.blinkThread = Thread(target=self.__blinkMonitor, daemon=True)
    logging.debug("bear constructor finished")

  def __del__(self):
    logging.debug("bear deconstructor finished")

  def activate(self):
    self.isRunning = True

    #set starting motor positions
    self.eyes.open()
    self.mouth.close()

    self.talkThread.start()
    self.blinkThread.start()
    logging.debug("bear instance activated")

  def deactivate(self):
    self.isRunning = False
    self.isTalking = False

    #set resting motor positions
    self.eyes.close()
    self.mouth.close()

    logging.debug("bear instance deactivated")

  def __talkMonitor(self):
    lastMouthEvent = 0
    lastMouthEventTime = 0
    while self.isRunning:
      if self.isTalking:
        if( self.audio.mouthValue != lastMouthEvent ):
          lastMouthEvent = self.audio.mouthValue
          lastMouthEventTime = time.time()

          if( self.audio.mouthValue == 1 ):
            self.mouth.setDirection('opening')
          else:
            self.mouth.setDirection('closing')
        else:
          if( time.time() - lastMouthEventTime > 0.4 ):
            self.mouth.setDirection('brake')
        sleep(.02)
      else:
        sleep(.1)

  def __blinkMonitor(self):
    while self.isRunning:
      if self.isTalking:
        sleep(random.randint(1,3))
        self.eyes.close()
        sleep(.2)
        self.eyes.open()
      else:
        sleep(.1)

  def update(self, data):
    if self.isTalking:
      logging.error('cannot update bear while it is talking')
    else:
      if 'eyes' in data:
        if data['eyes'] == True and self.eyes.state != 'open': self.eyes.open()
        elif data['eyes'] == False and self.eyes.state != 'closed': self.eyes.close()
      if 'mouth' in data:
        if data['mouth'] == True and self.mouth.state != 'open': self.mouth.open()
        elif data['mouth'] == False and self.mouth.state != 'closed': self.mouth.close()

  def play(self, filename):
    self.isTalking = True
    self.mouth.setDirection('brake')
    self.mouth.pwm.start(self.mouth.speed)
    if filename == 'espeak':
      self.audio.play("espeak.wav")
    else:
      self.audio.play("public/sounds/"+filename+".wav")
    self.isTalking = False
    self.mouth.stop()

  def say(self, text):
    # TODO: make speech params configurable
    subprocess.run([
      "espeak", 
      "-w","espeak.wav",
      "-s","125", 
      "-v","en+m3",
      "-p","25",
      "-a","175", 
      text
    ])
    logging.debug('espeak ran')
    self.play("espeak")