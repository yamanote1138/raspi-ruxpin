#!/usr/bin/env python
import RPi.GPIO as GPIO
import time

# set config variables
pwm_freq = 2000
pwm_pin = 18
dir_pin = 14
cdir_pin = 23
speed = 100
duration = .5

# use Broadcom pin designations
GPIO.setmode(GPIO.BCM)

# designate pins as OUT
GPIO.setup(pwm_pin, GPIO.OUT)
GPIO.setup(dir_pin, GPIO.OUT)
GPIO.setup(cdir_pin, GPIO.OUT)

# initialize PWM
pwm = GPIO.PWM(pwm_pin, pwm_freq)

# set pin levels
GPIO.output(dir_pin, GPIO.HIGH)
GPIO.output(cdir_pin, GPIO.LOW)

pwm.start(speed)
time.sleep(duration)
pwm.stop()

# unset pin levels
GPIO.output(dir_pin, GPIO.LOW)
GPIO.output(cdir_pin, GPIO.LOW)

GPIO.cleanup()