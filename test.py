#!/usr/bin/env python
import sys
import getopt
import RPi.GPIO as GPIO
import time

def main(argv):
  motor = ''
  direction = ''
  speed = 0

  try:
    opts, args = getopt.getopt(argv,"hm:d:s:")
  except getopt.GetoptError:
    print('test.py -m motor -d direction -s speed')
    sys.exit(2)
  for opt, arg in opts:
      if opt == '-h':
        print('test.py -m motor -d direction -s speed')
        sys.exit()
      elif opt=="-m":
        motor = arg
      elif opt =="-d":
        direction = arg
      elif opt=="-s":
        speed = int(arg)
  
  print('motor: {}\ndirection: {}\nspeed: {}\n'.format(motor, direction, speed))

# # set config variables
# pwm_freq = 2000
# pwm_pin = 18
# dir_pin = 14
# cdir_pin = 23
# speed = 100
# duration = .5

# # use Broadcom pin designations
# GPIO.setmode(GPIO.BCM)

# # designate pins as OUT
# GPIO.setup(pwm_pin, GPIO.OUT)
# GPIO.setup(dir_pin, GPIO.OUT)
# GPIO.setup(cdir_pin, GPIO.OUT)

# # initialize PWM
# pwm = GPIO.PWM(pwm_pin, pwm_freq)

# # set pin levels
# GPIO.output(dir_pin, GPIO.HIGH)
# GPIO.output(cdir_pin, GPIO.LOW)

# pwm.start(speed)
# time.sleep(duration)
# pwm.stop()

# # unset pin levels
# GPIO.output(dir_pin, GPIO.LOW)
# GPIO.output(cdir_pin, GPIO.LOW)

# GPIO.cleanup()

if __name__ == "__main__":
  main(sys.argv[1:])