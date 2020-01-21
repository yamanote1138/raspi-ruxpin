#!/usr/bin/env python
import RPi.GPIO as GPIO
import subprocess
import time

from servo import Servo

from random import randint
from threading import Thread

isRunning = False

class Bear:
  def __init__(self, config, audio):
    GPIO.cleanup()
    # use Broadcom pin designations
    GPIO.setmode(GPIO.BCM)

    # attach audio player
    self.audio = audio

    # add list of supported phrases
    self.phrases = config.phrases

    # bind mouth and eye servos based on pins defined in config
    self.eyes = Servo(config.getint('pins', 'pwma'), config.getint('pins', 'ain1'), config.getint('pins', 'ain2'), 'eyes')
    self.mouth = Servo(config.getint('pins', 'pwmb'), config.getint('pins', 'bin1'), config.getint('pins', 'bin2'), 'mouth')

    # self.mouthThread = None
    # self.eyesThread = None
    # self.mouthThread = Thread(target=self.__updateMouth)
    # self.mouthThread.start()

    isRunning = True
    print("initialized Bear instance")

  def __del__(self):
    # if self.mouthThread != None: self.mouthThread.stop()
    # if self.eyesThread != None: self.eyesThread.stop()
    GPIO.cleanup()
    print("deinitialized Bear instance")

  #observe audio signal and move mouth accordingly
  # def __updateMouth(self):
  #   lastMouthEvent = 0
  #   lastMouthEventTime = 0

  #   while( self.audio == None ):
  #     time.sleep( 0.1 )

  #   while isRunning:
  #     if( self.audio.mouthValue != lastMouthEvent ):
  #       lastMouthEvent = self.audio.mouthValue
  #       lastMouthEventTime = time.time()

  #       if( self.audio.mouthValue == 1 ):
  #         self.mouth.open()
  #       else:
  #         self.mouth.close()
  #     elif( time.time() - lastMouthEventTime > 0.4 ):
  #       self.mouth.stop()

  def update(self, data):
    if('eyes' in data['bear']): self.eyes.move(opening=data['bear']['eyes']['open'])
    if('mouth' in data['bear']): self.mouth.move(opening=data['bear']['mouth']['open'])
    return self.getStatus()

  def getStatus(self):
    print(self)
    return { "bear": { "eyes": { "open": self.eyes.open }, "mouth": { "open": self.mouth.open } } }

  def play(self, filename):
    if(self.audio!=None):
      print("playing audio file %s", (filename))
      self.audio.play("public/sounds/"+filename+".wav")

  def talk(self, text):
    # Sometimes the beginning of audio can get cut off. Insert silence.
    os.system( "espeak \",...\" 2>/dev/null" )
    time.sleep( 0.5 )
    # TODO: make speech params configurable
    subprocess.call(["espeak", "-w", "speech.wav", text, "-s", "130", "-a", "200", "-ven-us+m3","-g","5"])
    self.audio.play("speech.wav")

