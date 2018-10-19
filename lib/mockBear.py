#!/usr/bin/env python
class Servo:
  def __init__(self, open_pin, close_pin, label="unknown"):
    self.open = None
    self.label = label
    print("Servo inited (open_pin=%s, close_pin=%s)" % (open_pin, close_pin))

  def move(self, opening=True, duration=.5):
    if(opening and (self.open == None or not self.open)):
      self.open = True
      print("opened %s servo" % self.label)
    else:
      self.open = False
      print("closed %s servo" % self.label)

  def stop(self):
    print("stopped %s servo" % self.label)

class Bear:
  def __init__(self, config, audio=None):
    # add list of supported phrases
    self.phrases = config.phrases

    self.mouth = Servo(config.getint('pins', 'mouth_open'), config.getint('pins', 'mouth_closed'), "mouth")
    self.eyes = Servo(config.getint('pins', 'eyes_open'), config.getint('pins', 'eyes_closed'), "eyes")

    # set initial motor state
    self.eyes.move(True)
    self.mouth.move(False)

  def update(self, data):
    if('eyes' in data['bear']): self.eyes.move(opening=data['bear']['eyes']['open'])
    if('mouth' in data['bear']): self.mouth.move(opening=data['bear']['mouth']['open'])
    return self.getStatus()

  def getStatus(self):
    return { "bear": { "eyes": { "open": self.eyes.open }, "mouth": { "open": self.mouth.open } } }

  def blink():
    print("Bear.blink()")

  def play(self, filename):
    print("Bear.play() : \"%s\"" % filename)

  def talk(self, text):
    print("Bear.talk() : \"%s\"" % text)
