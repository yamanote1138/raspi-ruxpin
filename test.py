import ConfigParser
import RPi.GPIO as GPIO
import time

# read config file
config = ConfigParser.RawConfigParser()
config.read('main.cfg')

# map configured pins to variables
MOUTH_OPEN = config.get('pins', 'mouth_open')
MOUTH_CLOSED = config.get('pins', 'mouth_closed')
EYES_OPEN = config.get('pins', 'eyes_open')
EYES_CLOSED = config.get('pins', 'eyes_closed')

# set gpio to map pins using board numbers (as opposed to bcm names)
GPIO.setmode(GPIO.BOARD)

# designate pins as OUT
GPIO.setup(MOUTH_OPEN, GPIO.OUT)
GPIO.setup(MOUTH_CLOSED, GPIO.OUT)
GPIO.setup(EYES_OPEN, GPIO.OUT)
GPIO.setup(EYES_CLOSED, GPIO.OUT)

# open the mouth and eyes
GPIO.output(MOUTH_OPEN, GPIO.HIGH)
GPIO.output(MOUTH_CLOSED, GPIO.LOW)
GPIO.output(EYES_OPEN, GPIO.HIGH)
GPIO.output(EYES_CLOSED, GPIO.LOW)

# wait a second
time.sleep(1)

# close the mouth and eyes
GPIO.output(MOUTH_OPEN, GPIO.LOW)
GPIO.output(MOUTH_CLOSED, GPIO.HIGH)
GPIO.output(EYES_OPEN, GPIO.LOW)
GPIO.output(EYES_CLOSED, GPIO.HIGH)

# wait a second
time.sleep(1)

# set all pins used to off (just to be safe)
GPIO.output(MOUTH_OPEN, GPIO.LOW)
GPIO.output(MOUTH_CLOSED, GPIO.LOW)
GPIO.output(EYES_OPEN, GPIO.LOW)
GPIO.output(EYES_CLOSED, GPIO.LOW)

# clear pin settings
GPIO.cleanup()