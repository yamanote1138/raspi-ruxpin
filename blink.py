import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

GPIO.setup(13, GPIO.OUT)
GPIO.output(13, GPIO.HIGH)

time.sleep(3)

GPIO.output(13, GPIO.LOW)
GPIO.cleanup()