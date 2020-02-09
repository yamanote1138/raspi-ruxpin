#!/usr/bin/env python
import RPi.GPIO as GPIO
import os
import subprocess
import time

from servo import Servo

from random import randint
from threading import Thread

class Bear:
  def __init__(self, config, audio):
    GPIO.cleanup()
    # use Broadcom pin designations
    GPIO.setmode(GPIO.BCM)

    self.isRunning = True
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

    # self.eyesThread = None
    # self.mouthThread = None
    self.mouthThread = Thread(target=self.__updateMouth)
    self.mouthThread.start()

    print("initialized Bear instance")

  def __del__(self):
    # if self.eyesThread != None: self.eyesThread.stop()
    self.isRunning = False
    if self.mouthThread != None: self.mouthThread.stop()
    GPIO.cleanup()
    print("deinitialized Bear instance")

  #observe audio signal and move mouth accordingly
  def __updateMouth(self):
    lastMouthEvent = 0
    lastMouthEventTime = time.time()

    while self.isRunning:
      if self.isTalking:
        if( self.audio.mouthValue != lastMouthEvent ):
          lastMouthEvent = self.audio.mouthValue
          lastMouthEventTime = time.time()

          if( self.audio.mouthValue == 1 ):
            self.mouth.open()
          else:
            self.mouth.close()
        elif( time.time() - lastMouthEventTime > 0.4 ):
          self.mouth.stop()

  def update(self, data):
    if('eyes' in data['bear']): self.eyes.move(opening=data['bear']['eyes']['open'])
    if('mouth' in data['bear']): self.mouth.move(opening=data['bear']['mouth']['open'])
    return self.getStatus()

  def getStatus(self):
    print(self)
    return { "bear": { "eyes": { "open": self.eyes.open }, "mouth": { "open": self.mouth.open } } }

  def play(self, filename):
    self.isTalking = True
    self.audio.play("public/sounds/"+filename+".wav")
    self.isTalking = False

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

