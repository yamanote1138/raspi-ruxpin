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
  duration = .5

  try:
    opts, args = getopt.getopt(argv,"hm:ocs:d:")
  except getopt.GetoptError:
    print('test.py -m motor -o/c -s speed -d duration')
    sys.exit(2)
  for opt, arg in opts:
      if opt == '-h':
        print('test.py -m motor -o/c -s speed -d duration')
        sys.exit()
      elif opt=="-m":
        motor = arg
      elif opt =="-o":
        direction = 'open'
      elif opt =="-c":
        direction = 'closed'
      elif opt=="-s":
        speed = int(arg)
      elif opt=="-d":
        duration = float(arg)
  
  print('arguments:\nmotor: {}\ndirection: {}\nspeed: {}\nduration: {}\n'.format(motor, direction, speed, duration))

  # set config variables
  PWMA = 18
  AIN1 = 24
  AIN2 = 23

  PWMB = 17
  BIN1 = 22
  BIN2 = 27

  speed = 100
  duration = .5

  # use Broadcom pin designations
  GPIO.setmode(GPIO.BCM)

  pwm_pin = None
  dir_pin = None
  cdir_pin = None

  # set up motor pins
  if(motor=='eyes'):
    pwm_pin = PWMA
    dir_pin = AIN1
    cdir_pin = AIN2
  else:
    pwm_pin = PWMB
    dir_pin = BIN1
    cdir_pin = BIN2

  GPIO.setup(pwm_pin, GPIO.OUT)
  GPIO.setup(dir_pin, GPIO.OUT)
  GPIO.setup(cdir_pin, GPIO.OUT)

  # set pin levels
  if(direction=='open'):
    GPIO.output(dir_pin, GPIO.HIGH)
    GPIO.output(cdir_pin, GPIO.LOW)
  else:
    GPIO.output(dir_pin, GPIO.LOW)
    GPIO.output(cdir_pin, GPIO.HIGH)

  # pwm = GPIO.PWM(pwm_pin, pwm_freq)
  # pwm.start(speed)
  # time.sleep(duration)
  # pwm.stop()

  GPIO.output(pwm_pin, GPIO.HIGH)
  time.sleep(duration)
  GPIO.output(pwm_pin, GPIO.LOW)
  
  print('done')

  # unset pin levels
  GPIO.output(pwm_pin, GPIO.LOW)
  GPIO.output(dir_pin, GPIO.LOW)
  GPIO.output(cdir_pin, GPIO.LOW)

  GPIO.cleanup()

  print('cleanup')


if __name__ == "__main__":
  main(sys.argv[1:])