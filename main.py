#!/usr/bin/python
# based on Chippy Ruxpin by Next Thing Co

# apt-get install python-setuptools python-dev build-essential espeak alsa-utils
# apt-get install python-alsaaudio python-numpy python-twitter python-bottle mplayer

import sys
import time
import subprocess
import os
from random import randint
from threading import Thread
from lib.audioPlayer import AudioPlayer
from lib.gpio import GPIO
from lib.webFramework import WebFramework

fullMsg = ""

MOUTH_OPEN = 1013 # GPIO pin assigned to open the mouth. XIO-P0
MOUTH_CLOSE = 1015 # GPIO pin assigned to close the mouth. XIO-P2
EYES_OPEN = 1019 # GPIO pin assigned to open the eyes. XIO-P4
EYES_CLOSE = 1017 # GPIO pin assigned to close the eyes. XIO-P6

io = GPIO() #Establish connection to our GPIO pins.
io.setup( MOUTH_OPEN )
io.setup( EYES_OPEN )
io.setup( MOUTH_CLOSE )
io.setup( EYES_CLOSE )

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
                io.set( MOUTH_OPEN, 1 )
                io.set( MOUTH_CLOSE, 0 )
            else:
                io.set( MOUTH_OPEN, 0 )
                io.set( MOUTH_CLOSE, 1 )
        else:
            if( time.time() - lastMouthEventTime > 0.4 ):
                io.set( MOUTH_OPEN, 0 )
                io.set( MOUTH_CLOSE, 0 )

# A routine for blinking the eyes in a semi-random fashion.
def updateEyes():
    while isRunning:
        io.set( EYES_CLOSE, 1 )
        io.set( EYES_OPEN, 0 )
        time.sleep(0.4)
        io.set( EYES_CLOSE, 0 )
        io.set( EYES_OPEN, 1 )
        time.sleep(0.4)
        io.set( EYES_CLOSE, 1 )
        io.set( EYES_OPEN, 0 )
        time.sleep(0.4)
        io.set( EYES_CLOSE, 0 )
        io.set( EYES_OPEN, 0 )
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

mouthThread = Thread(target=updateMouth)
mouthThread.start()
eyesThread = Thread(target=updateEyes)
eyesThread.start()     
audio = AudioPlayer()

web = WebFramework(talk, phrase)
isRunning = False
io.cleanup()
sys.exit(1)
