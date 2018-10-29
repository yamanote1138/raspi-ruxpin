#!/usr/bin/env python
import argparse
import ConfigParser
import os
import time

parser = argparse.ArgumentParser(description='testing open/close of bear motors')
parser.add_argument("-e", "--eyes", choices=["open", "close", "o", "c"], help="position of eyes")
parser.add_argument("-m", "--mouth", choices=["open", "close", "o", "c"], help="position of mouth")
args = parser.parse_args()

eyes = 'open' if args.eyes in ["open", "o"] else 'closed'
mouth = 'open' if args.mouth in ["open", "o"] else 'closed'

# read main config file
config = ConfigParser.RawConfigParser()
config.read('config/main.cfg')

if(eyes == 'open'):
  eyes_pin = config.getint('pins', 'eyes_open')
else:
  eyes_pin = config.getint('pins', 'eyes_closed')

if(mouth == 'open'):
  mouth_pin = config.getint('pins', 'mouth_open')
else:
  mouth_pin = config.getint('pins', 'mouth_closed')

# print debug output
print("setting eyes to %s via pin %s" % (eyes, eyes_pin))
print("setting mouth to %s via pin %s" % (mouth, mouth_pin))

IS_PI = os.uname()[4][:3] == 'arm'

if(IS_PI):

  import RPi.GPIO as GPIO

  # set GPIO to BCM (Broadcom) pin numbering
  GPIO.setmode(GPIO.BCM)

  # set eye and mouth GPIO pins to output mode
  GPIO.setup(epin, GPIO.OUT)
  GPIO.setup(mpin, GPIO.OUT)

  # activate selected GPIO pins
  GPIO.output(epin, GPIO.HIGH)
  GPIO.output(mpin, GPIO.HIGH)

  # wait a half-second
  time.sleep(.5)

  # deactivate selected GPIO pins
  GPIO.output(epin, GPIO.LOW)
  GPIO.output(mpin, GPIO.LOW)

  # reset GPIO state
  GPIO.cleanup()
