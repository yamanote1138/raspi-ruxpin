#!/usr/bin/python

import sys
import time
import subprocess
import os
import ConfigParser

from random import randint
from threading import Thread

import RPi.GPIO as GPIO

from lib.webPuppet import WebPuppet

# read main config file
config = ConfigParser.RawConfigParser()
config.read('main.cfg')

# map configured pins to variables
MOUTH_OPEN = config.getint('pins', 'mouth_open')
MOUTH_CLOSED = config.getint('pins', 'mouth_closed')
EYES_OPEN = config.getint('pins', 'eyes_open')
EYES_CLOSED = config.getint('pins', 'eyes_closed')

# use Broadcom pin designations
GPIO.setmode(GPIO.BCM)

# designate pins as OUT
GPIO.setup(MOUTH_OPEN, GPIO.OUT)
GPIO.setup(MOUTH_CLOSED, GPIO.OUT)
GPIO.setup(EYES_OPEN, GPIO.OUT)
GPIO.setup(EYES_CLOSED, GPIO.OUT)

def moveMouth(open=True):
  if(open):
    GPIO.output( MOUTH_OPEN, GPIO.HIGH )
    GPIO.output( MOUTH_CLOSED, GPIO.LOW )
    time.sleep(1)
    GPIO.output( MOUTH_OPEN, GPIO.LOW )
    GPIO.output( MOUTH_CLOSED, GPIO.LOW )
  else:
    GPIO.output( MOUTH_OPEN, GPIO.LOW )
    GPIO.output( MOUTH_CLOSED, GPIO.HIGH )
    time.sleep(1)
    GPIO.output( MOUTH_OPEN, GPIO.LOW )
    GPIO.output( MOUTH_CLOSED, GPIO.LOW )

def moveEyes(open=True):
  if(open):
    GPIO.output( EYES_OPEN, GPIO.HIGH )
    GPIO.output( EYES_CLOSED, GPIO.LOW )
    time.sleep(1)
    GPIO.output( EYES_OPEN, GPIO.LOW )
    GPIO.output( EYES_CLOSED, GPIO.LOW )
  else:
    GPIO.output( EYES_OPEN, GPIO.LOW )
    GPIO.output( EYES_CLOSED, GPIO.HIGH )
    time.sleep(1)
    GPIO.output( EYES_OPEN, GPIO.LOW )
    GPIO.output( EYES_CLOSED, GPIO.LOW )

web = WebPuppet(moveMouth, moveEyes)

GPIO.cleanup()
sys.exit(1)
