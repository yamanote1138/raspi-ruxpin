#!/usr/bin/env python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(24, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)

GPIO.output(24, GPIO.HIGH)
GPIO.output(27, GPIO.HIGH)

time.sleep(.5)

GPIO.output(24, GPIO.LOW)
GPIO.output(27, GPIO.LOW)

GPIO.cleanup()
