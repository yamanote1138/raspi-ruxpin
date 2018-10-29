#!/usr/bin/env python
import argparse
import time
import RPi.GPIO as GPIO

parser = argparse.ArgumentParser(description='testing open/close of bear motors')
parser.add_argument("-s", "--servo", choices=["eyes", "mouth"],
                    help='which servo to operate')
parser.add_argument("-d", "--direction", choices=["open", "close"],
                    help='which direction to move')

args = parser.parse_args()
print("setting %s to %s" % (args.servo, args.direction))

EO_PIN = 23
EC_PIN = 24
MO_PIN = 17
MC_PIN = 27

if(args.servo == 'eyes'):
  if(args.direction == 'open'):
    pin = EO_PIN
  else:
    pin = EC_PIN
else:
  if(args.direction == 'open'):
    pin = MO_PIN
  else:
    pin = MC_PIN

GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.OUT)
GPIO.output(pin, GPIO.HIGH)
time.sleep(.5)
GPIO.output(pin, GPIO.LOW)

GPIO.cleanup()
