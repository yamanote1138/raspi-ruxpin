#!/usr/bin/env python
import sys
import getopt
import RPi.GPIO as GPIO
import time

def main(argv):
  motor = 'eyes'
  direction = 'open'
  speed = 100
  pwm_freq = 2000

  try:
    opts, args = getopt.getopt(argv,"hm:ocs:")
  except getopt.GetoptError:
    print('test.py -m motor -o/c -s speed')
    sys.exit(2)
  for opt, arg in opts:
      if opt == '-h':
        print('test.py -m motor -o/c -s speed')
        sys.exit()
      elif opt=="-m":
        motor = arg
      elif opt =="-o":
        direction = 'open'
      elif opt =="-c":
        direction = 'closed'
      elif opt=="-s":
        speed = int(arg)
  
  print('arguments:\nmotor: {}\ndirection: {}\nspeed: {}\n'.format(motor, direction, speed))

  # set config variables
  pwma_pin = 18
  dira_pin = 24
  cdira_pin = 23

  pwmb_pin = 17
  dirb_pin = 22
  cdirb_pin = 27

  speed = 100
  duration = .5

  # use Broadcom pin designations
  GPIO.setmode(GPIO.BCM)

  pwm_pin = None
  dir_pin = None
  cdir_pin = None

  # set up motor pins
  if(motor=='eyes'):
    pwm_pin = pwma_pin
    dir_pin = dira_pin
    cdir_pin = cdira_pin
  else:
    pwm_pin = pwmb_pin
    dir_pin = dirb_pin
    cdir_pin = cdirb_pin

  GPIO.setup(pwm_pin, GPIO.OUT)
  GPIO.setup(dir_pin, GPIO.OUT)
  GPIO.setup(cdir_pin, GPIO.OUT)
  pwm = GPIO.PWM(pwm_pin, pwm_freq)

  # set pin levels
  if(direction=='open'):
    GPIO.output(dir_pin, GPIO.HIGH)
    GPIO.output(cdir_pin, GPIO.LOW)
  else:
    GPIO.output(dir_pin, GPIO.LOW)
    GPIO.output(cdir_pin, GPIO.HIGH)

  pwm.start(speed)
  time.sleep(duration)
  pwm.stop()

  # unset pin levels
  GPIO.output(dir_pin, GPIO.LOW)
  GPIO.output(cdir_pin, GPIO.LOW)

  GPIO.cleanup()

if __name__ == "__main__":
  main(sys.argv[1:])