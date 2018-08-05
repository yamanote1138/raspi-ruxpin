#!/usr/bin/python
# based on Chippy Ruxpin by Next Thing Co

import sys
import time
import subprocess
import os

from random import randint
from threading import Thread

import RPi.GPIO as GPIO

from lib.audioPlayer import AudioPlayer
from lib.webFramework import WebFramework

fullMsg = ""

GPIO.setmode(GPIO.BOARD)

MOUTH_OPEN = 7
GPIO.setup(MOUTH_OPEN, GPIO.OUT, initial = 0)
MOUTH_CLOSE = 11
GPIO.setup(MOUTH_CLOSE, GPIO.OUT, initial = 0)
EYES_OPEN = 13
GPIO.setup(EYES_OPEN, GPIO.OUT, initial = 0)
EYES_CLOSE = 15
GPIO.setup(EYES_CLOSE, GPIO.OUT, initial = 0)

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
                GPIO.output( MOUTH_CLOSE, GPIO.LOW )
            else:
                GPIO.output( MOUTH_OPEN, GPIO.LOW )
                GPIO.output( MOUTH_CLOSE, GPIO.HIGH )
        else:
            if( time.time() - lastMouthEventTime > 0.4 ):
                GPIO.output( MOUTH_OPEN, GPIO.LOW )
                GPIO.output( MOUTH_CLOSE, GPIO.LOW )

# A routine for blinking the eyes in a semi-random fashion.
def updateEyes():
    while isRunning:
        GPIO.output( EYES_CLOSE, 1 )
        GPIO.output( EYES_OPEN, 0 )
        time.sleep(0.4)
        GPIO.output( EYES_CLOSE, 0 )
        GPIO.output( EYES_OPEN, 1 )
        time.sleep(0.4)
        GPIO.output( EYES_CLOSE, 1 )
        GPIO.output( EYES_OPEN, 0 )
        time.sleep(0.4)
        GPIO.output( EYES_CLOSE, 0 )
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

# mouthThread = Thread(target=updateMouth)
# mouthThread.start()
# eyesThread = Thread(target=updateEyes)
# eyesThread.start()     
audio = AudioPlayer()

web = WebFramework(talk, phrase)
isRunning = False
GPIO.cleanup()
sys.exit(1)
