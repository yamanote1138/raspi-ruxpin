#!/usr/bin/env python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(17, GPIO.OUT)

GPIO.output(23, GPIO.HIGH)
GPIO.output(17, GPIO.HIGH)

time.sleep(.5)

GPIO.output(23, GPIO.LOW)
GPIO.output(17, GPIO.LOW)

GPIO.cleanup()
