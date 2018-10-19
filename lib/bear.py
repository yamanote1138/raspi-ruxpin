#!/usr/bin/env python
import RPi.GPIO as GPIO
import subprocess
import time

from random import randint
from threading import Thread

class Servo:
  def __init__(self, open_pin, close_pin, label="unknown"):
    # map configured pins to variables
    self.open_pin = open_pin
    self.close_pin = close_pin
    self.open = None
    self.label = label

    # designate pins as OUT
    GPIO.setup(self.open_pin, GPIO.OUT)
    GPIO.setup(self.close_pin, GPIO.OUT)

  def move(self, opening=True, duration=.5):
    if(opening and (self.open == None or not self.open)):
      GPIO.output( self.open_pin, GPIO.HIGH )
      GPIO.output( self.close_pin, GPIO.LOW )
      if(duration!=None):
        time.sleep(duration)
        self.stop()
      self.open = True
    else:
      GPIO.output( self.open_pin, GPIO.LOW )
      GPIO.output( self.close_pin, GPIO.HIGH )
      if(duration!=None):
        time.sleep(.5)
        self.stop()
      self.open = False

  def stop(self):
    GPIO.output( self.open_pin, GPIO.LOW )
    GPIO.output( self.close_pin, GPIO.LOW )

class Bear:
  def __init__(self, config, audio):
    # use Broadcom pin designations
    GPIO.setmode(GPIO.BCM)

    # attach audio player
    self.audio = audio

    # add list of supported phrases
    self.phrases = config.phrases

    # bind mouth and eye servos based on pins defined in config
    self.mouth = Servo(config.getint('pins', 'mouth_open'), config.getint('pins', 'mouth_closed'))
    self.eyes = Servo(config.getint('pins', 'eyes_open'), config.getint('pins', 'eyes_closed'))

    # set initial motor state
    self.eyes.move(True)
    self.mouth.move(False)

    # self.mouthThread = Thread(target=_updateMouth)
    # self.mouthThread.start()

  # observe audio signal and move mouth accordingly
  def _updateMouth():
    lastMouthEvent = 0
    lastMouthEventTime = 0

    while( self.audio == None ):
      time.sleep( 0.1 )

    while isRunning:
      if( self.audio.mouthValue != lastMouthEvent ):
        lastMouthEvent = self.audio.mouthValue
        lastMouthEventTime = time.time()

        if( self.audio.mouthValue == 1 ):
          self.mouth.move(opening=True, duration=None)
        else:
          self.mouth.move(opening=False, duration=None)
      elif( time.time() - lastMouthEventTime > 0.4 ):
        self.mouth.stop()

  def update(self, data):
    if('eyes' in data['bear']): self.eyes.move(opening=data['bear']['eyes']['open'])
    if('mouth' in data['bear']): self.mouth.move(opening=data['bear']['mouth']['open'])
    return self.getStatus()

  def getStatus(self):
    return { "bear": { "eyes": { "open": self.eyes.open }, "mouth": { "open": self.mouth.open } } }

  def blink():
    self.eyes.move(opening=True)
    time.sleep(0.4)
    self.eyes.move(opening=False)
    time.sleep(0.4)
    self.eyes.move(opening=True)
    time.sleep(0.4)
    self.eyes.move(opening=False)

  def play(filename):
    self.audio.play("public/sounds/"+filename+".wav")

  def talk(text):
    # Sometimes the beginning of audio can get cut off. Insert silence.
    os.system( "espeak \",...\" 2>/dev/null" )
    time.sleep( 0.5 )
    # TODO: make speech params configurable
    subprocess.call(["espeak", "-w", "speech.wav", text, "-s", "130", "-a", "200", "-ven-us+m3","-g","5"])
    self.audio.play("speech.wav")

  def __del__(self):
    if self.mouthThread != None: self.mouthThread.stop()
    if self.eyesThread != None: self.eyesThread.stop()
    GPIO.cleanup()
