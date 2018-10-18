#!/usr/bin/env python
class Servo:
  def __init__(self, open_pin, close_pin):
    print("Servo inited (open_pin=%s, close_pin=%s)" % (open_pin, close_pin))

  def open(self, duration=.5):
    print("Servo.open()")

  def close(self, duration=.5):
    print("Servo.close()")

  def stop(self):
    print("Servo.stop()")

class Bear:
  def __init__(self, config, audio=None):
    self.mouth = Servo(config.getint('pins', 'mouth_open'), config.getint('pins', 'mouth_closed'))
    self.eyes = Servo(config.getint('pins', 'eyes_open'), config.getint('pins', 'eyes_closed'))

  def blink():
    print("Bear.blink()")

  def phrase(filename):
    print("Bear.phrase() : \"%s\"" % filename)

  def talk(text):
    print("Bear.talk() : \"%s\"" % text)

  def __del__(self):
    self.mouthThread.stop()
    self.eyesThread.stop()
    GPIO.cleanup()
