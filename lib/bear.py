#!/usr/bin/env python
import RPi.GPIO as GPIO
import subprocess
import time

from random import randint
from threading import Thread

class Servo:
  def __init__(self, open_pin, close_pin):
    # map configured pins to variables
    self.open_pin = open_pin
    self.close_pin = close_pin
    self.is_open = None

    # designate pins as OUT
    GPIO.setup(self.open_pin, GPIO.OUT)
    GPIO.setup(self.close_pin, GPIO.OUT)

  def open(self):
    if(not self.is_open):
      GPIO.output( self.open_pin, GPIO.HIGH )
      GPIO.output( self.close_pin, GPIO.LOW )
      self.is_open = True
      time.sleep(.5)
      GPIO.output( self.open_pin, GPIO.LOW )
      GPIO.output( self.close_pin, GPIO.LOW )

  def close(self):
    if(self.is_open):
      GPIO.output( self.open_pin, GPIO.LOW )
      GPIO.output( self.close_pin, GPIO.HIGH )
      self.is_open = False
      time.sleep(.5)
      GPIO.output( self.open_pin, GPIO.LOW )
      GPIO.output( self.close_pin, GPIO.LOW )

class Bear:
  def __init__(self, config, audio):
    # use Broadcom pin designations
    GPIO.setmode(GPIO.BCM)

    # attach audio player
    self.audio = audio

    # bind mouth and eye servos based on pins defined in config
    self.mouth = Servo(config.getint('pins', 'mouth_open'), config.getint('pins', 'mouth_closed'))
    self.eyes = Servo(config.getint('pins', 'eyes_open'), config.getint('pins', 'eyes_closed'))

    # set initial motor state

    self.mouthThread = Thread(target=_updateMouth)
    self.mouthThread.start()

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
          self.mouth.open(duration=None)
        else:
          self.mouth.close(duration=None)
      elif( time.time() - lastMouthEventTime > 0.4 ):
        self.mouth.stop()

  def blink():
    self.eyes.open()
    time.sleep(0.4)
    self.eyes.close()
    time.sleep(0.4)
    self.eyes.open()
    time.sleep(0.4)
    self.eyes.stop()

  def phrase(filename):
    self.audio.play("sounds/"+filename+".wav")

  def talk(text):
    os.system( "espeak \",...\" 2>/dev/null" ) # Sometimes the beginning of audio can get cut off. Insert silence.
    time.sleep( 0.5 )
    # TODO: make speech params configurable
    subprocess.call(["espeak", "-w", "speech.wav", text, "-s", "130", "-a", "200", "-ven-us+m3","-g","5"])
    self.audio.play("speech.wav")

  def __del__(self):
    self.mouthThread.stop()
    self.eyesThread.stop()
    GPIO.cleanup()
