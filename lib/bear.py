#!/usr/bin/env python
import os
import subprocess
import time

from servo import Servo
from random import randint
from threading import Thread

class Bear:
  def __init__(self, config, audio):
    self.isRunning = True
    self.isPuppet = True
    self.isTalking = False

    # attach audio player
    self.audio = audio

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

    #set starting motor positions
    self.eyes.open()
    self.mouth.close()
    self.eyesThread = Thread(target=self.__updateEyes)
    self.mouthThread = Thread(target=self.__updateMouth)
    self.talkThread = Thread(target=self.__talkMonitor)
    print("bear constructor finished")

  def __del__(self):
    print("bear deconstructor finished")

  def activate(self):
    self.isRunning = True
    self.eyesThread.start()
    self.mouthThread.start()
    self.talkThread.start()
    print("bear instance activated")

  def deactivate(self):
    self.isRunning = False
    self.isPuppet = False
    self.isTalking = False
    print("bear instance deactivated")

  def __updateEyes(self):
    while self.isRunning:
      if self.isPuppet:
        if self.eyes.to == 'open' and self.eyes.state != 'open':
            self.eyes.open()
        elif self.eyes.to =='closed' and self.eyes.state != 'closed':
            self.eyes.close()
      time.sleep(.1)

  def __updateMouth(self):
    while self.isRunning:
      if self.isPuppet:
        if self.mouth.to == 'open' and self.mouth.state != 'open':
            self.mouth.open()
        elif self.mouth.to =='closed' and self.mouth.state != 'closed':
            self.mouth.close()
      time.sleep(.1)

  def __talkMonitor(self):
    lastMouthEvent = 0
    lastMouthEventTime = 0
    while self.isRunning:
      if self.isTalking:
        if( self.audio.mouthValue != lastMouthEvent ):
          lastMouthEvent = self.audio.mouthValue
          lastMouthEventTime = time.time()

          if( self.audio.mouthValue == 1 ):
            self.mouth.setDirection('open')
          else:
            self.mouth.setDirection('closed')
        else:
          if( time.time() - lastMouthEventTime > 0.4 ):
            self.mouth.setDirection('brake')
        # time.sleep(.05)
      else:
        time.sleep(.1)

  def update(self, data):
    if 'eyes' in data['bear']: self.eyes.to=data['bear']['eyes']['to']
    if 'mouth' in data['bear']: self.mouth.to=data['bear']['mouth']['to']

    # wait for slowest motor functions to complete before proceeding
    delayBuffer = .2
    if self.eyes.duration >= self.mouth.duration:
      time.sleep(self.eyes.duration + delayBuffer)
    else:
      time.sleep(self.mouth.duration + delayBuffer)

  def getStatus(self):
    return { "bear": { "eyes": { "state": self.eyes.state }, "mouth": { "state": self.mouth.state } } }

  def play(self, filename):
    self.isPuppet = False
    self.isTalking = True
    self.mouth.setDirection('brake')
    self.mouth.pwm.start(self.mouth.speed)
    self.audio.play("public/sounds/"+filename+".wav")
    self.mouth.stop()
    self.isTalking = False
    self.isPuppet = True

  def say(self, text):
    # Sometimes the beginning of audio can get cut off. Insert silence.
    os.system( "espeak \",...\" 2>/dev/null" )
    time.sleep( 0.5 )
    # TODO: make speech params configurable
    subprocess.call([
      "espeak", 
      "-w","speech.wav",
      "-s","125", 
      "-v","en+m3",
      "-p","25",
      "-a","150", 
      text
    ])
    self.audio.play("speech.wav")

