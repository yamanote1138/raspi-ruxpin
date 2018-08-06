#!/usr/bin/python
# based on Chippy Ruxpin by Next Thing Co

import sys
import time
import subprocess
import os
import ConfigParser
import json

from random import randint
from threading import Thread

import RPi.GPIO as GPIO

from lib.audioPlayer import AudioPlayer
from lib.webFramework import WebFramework

# read main config file
config = ConfigParser.RawConfigParser()
config.read('main.cfg')

# read phrases config file
with open('phrases.json', 'r') as f:
  phrases = json.load(f)

# map configured pins to variables
MOUTH_OPEN = config.getint('pins', 'mouth_open')
MOUTH_CLOSED = config.getint('pins', 'mouth_closed')
EYES_OPEN = config.getint('pins', 'eyes_open')
EYES_CLOSED = config.getint('pins', 'eyes_closed')

GPIO.setmode(GPIO.BOARD)

# designate pins as OUT
GPIO.setup(MOUTH_OPEN, GPIO.OUT)
GPIO.setup(MOUTH_CLOSED, GPIO.OUT)
GPIO.setup(EYES_OPEN, GPIO.OUT)
GPIO.setup(EYES_CLOSED, GPIO.OUT)

audio = None
isRunning = True

def updateMouth():
    lastMouthEvent = 0
    lastMouthEventTime = 0

    while( audio == None ):
        time.sleep( 0.1 )
        
    while isRunning:
        if( audio.mouthValue != lastMouthEvent ):
            lastMouthEvent = audio.mouthValue
            lastMouthEventTime = time.time()

            if( audio.mouthValue == 1 ):
                GPIO.output( MOUTH_OPEN, GPIO.HIGH )
                GPIO.output( MOUTH_CLOSED, GPIO.LOW )
            else:
                GPIO.output( MOUTH_OPEN, GPIO.LOW )
                GPIO.output( MOUTH_CLOSED, GPIO.HIGH )
        else:
            if( time.time() - lastMouthEventTime > 0.4 ):
                GPIO.output( MOUTH_OPEN, GPIO.LOW )
                GPIO.output( MOUTH_CLOSED, GPIO.LOW )

# A routine for blinking the eyes in a semi-random fashion.
def updateEyes():
    while isRunning:
        GPIO.output( EYES_CLOSED, 1 )
        GPIO.output( EYES_OPEN, 0 )
        time.sleep(0.4)
        GPIO.output( EYES_CLOSED, 0 )
        GPIO.output( EYES_OPEN, 1 )
        time.sleep(0.4)
        GPIO.output( EYES_CLOSED, 1 )
        GPIO.output( EYES_OPEN, 0 )
        time.sleep(0.4)
        GPIO.output( EYES_CLOSED, 0 )
        GPIO.output( EYES_OPEN, 0 )
        time.sleep( randint( 5,15) )
   
def phrase(myPhrase):
    audio.play("sounds/"+myPhrase+".wav")
    return myPhrase

def talk(myText):
    os.system( "espeak \",...\" 2>/dev/null" ) # Sometimes the beginning of audio can get cut off. Insert silence.
    time.sleep( 0.5 )
    subprocess.call(["espeak", "-w", "speech.wav", myText, "-s", "130", "-a", "200", "-ven-us+m3","-g","5"])
    audio.play("speech.wav")
    return myText

if(config.getboolean('options', 'move_mouth')):
    mouthThread = Thread(target=updateMouth)
    mouthThread.start()

if(config.getboolean('options', 'move_eyes')):
    eyesThread = Thread(target=updateEyes)
    eyesThread.start()     

audio = AudioPlayer()

web = WebFramework(talk, phrase, phrases)
isRunning = False
GPIO.cleanup()
sys.exit(1)
