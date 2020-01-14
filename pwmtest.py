#!/usr/bin/env python
import sys
import time
import RPi.GPIO as GPIO

# use Broadcom pin designations
GPIO.setmode(GPIO.BCM)

PWMA = 18; # motor A speed
AIN1 = 24; # motor A dir
AIN2 = 23; # motor A cdir

# designate pins as OUT
GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)

p = GPIO.PWM(PWMA, 0.5)

# open eyes
GPIO.output( AIN1, GPIO.HIGH )
GPIO.output( AIN2, GPIO.LOW )
p.start(1)
time.sleep(0.4)
p.stop()

# wait a half second
time.sleep(0.5)

#close eyes
GPIO.output( AIN1, GPIO.LOW )
GPIO.output( AIN2, GPIO.HIGH )
p.start(1)
time.sleep(0.4)
p.stop()

GPIO.cleanup()
