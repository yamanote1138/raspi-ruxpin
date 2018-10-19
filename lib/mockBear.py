#!/usr/bin/env python
class Servo:
  def __init__(self, open_pin, close_pin, label="unknown"):
    self.is_open = None
    self.label = label
    print("Servo inited (open_pin=%s, close_pin=%s)" % (open_pin, close_pin))

  def open(self, duration=.5):
    if(not self.is_open):
      print("opened %s servo" % self.label)

  def close(self, duration=.5):
    if(self.is_open):
      print("closed %s servo" % self.label)

  def stop(self):
    print("stopped %s servo" % self.label)

class Bear:
  def __init__(self, config, audio=None):
    self.mouth = Servo(config.getint('pins', 'mouth_open'), config.getint('pins', 'mouth_closed'), "mouth")
    self.eyes = Servo(config.getint('pins', 'eyes_open'), config.getint('pins', 'eyes_closed'), "eyes")

  def blink():
    print("Bear.blink()")

  def phrase(self, filename):
    print("Bear.phrase() : \"%s\"" % filename)

  def talk(self, text):
    print("Bear.talk() : \"%s\"" % text)

  def __del__(self):
    self.mouthThread.stop()
    self.eyesThread.stop()
    GPIO.cleanup()
