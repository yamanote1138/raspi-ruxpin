#!/usr/bin/env python
import argparse
import time
import RPi.GPIO as GPIO

parser = argparse.ArgumentParser(description='testing open/close of bear motors')
parser.add_argument("-e", "--eyes", choices=["open", "close", "o", "c"], help="position of eyes")
parser.add_argument("-m", "--mouth", choices=["open", "close", "o", "c"], help="position of mouth")

args = parser.parse_args()
print("setting %s to %s" % (args.servo, args.direction))

EO_PIN = 23
EC_PIN = 24
MO_PIN = 17
MC_PIN = 27

if(args.eyes == 'open' or args.eyes == 'o'):
  epin = EO_PIN
else:
  epin = EC_PIN

if(args.mouth == 'open' or args.mouth == 'o'):
  mpin = MO_PIN
else:
  mpin = MC_PIN

GPIO.setmode(GPIO.BCM)
GPIO.setup(epin, GPIO.OUT)
GPIO.setup(mpin, GPIO.OUT)
GPIO.output(epin, GPIO.HIGH)
GPIO.output(mpin, GPIO.HIGH)
time.sleep(.5)
GPIO.output(epin, GPIO.LOW)
GPIO.output(mpin, GPIO.LOW)

GPIO.cleanup()
