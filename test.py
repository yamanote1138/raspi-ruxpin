import RPi.GPIO as GPIO
import time


# PIN 11 (GPIO17) - MOUTH OPEN
# PIN 13 (GPIO27) - MOUTH CLOSED
# PIN 16 (GPIO23) - EYES OPEN
# PIN 18 (GPIO24) - EYES CLOSED

GPIO.setmode(GPIO.BOARD)

GPIO.setup(11, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)

GPIO.output(11, GPIO.HIGH)
GPIO.output(13, GPIO.LOW)

time.sleep(3)

GPIO.output(11, GPIO.LOW)
GPIO.output(13, GPIO.HIGH)

time.sleep(3)

GPIO.output(11, GPIO.LOW)
GPIO.output(13, GPIO.LOW)

GPIO.cleanup()