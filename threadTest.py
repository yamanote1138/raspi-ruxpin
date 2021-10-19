#!/usr/bin/env python
from threading import Thread
import time
import signal
import sys

class Servo:
  def __init__(self):
    #perform construction
    self.to = ''
    self.state = ''
    print("servo constructor finished")

  def __del__(self):
    #perform deconstruction
    print("servo deconstructor finished")

  def open(self):
    time.sleep(1)
    self.state = 'open'
    self.to = ''
    print("servo opened")

  def close(self):
    time.sleep(1)
    self.state = 'close'
    self.to = ''
    print("servo closed")

class Bear:
  def __init__(self):
    self.isRunning = False
    self.mouth = Servo()
    self.mouth.close()
    self.testThread = Thread(target=self.__updateMouth)
    print("bear constructor finished")

  def __del__(self):
    print("bear deconstructor finished")

  def activate(self):
    self.isRunning = True
    self.testThread.start()
    print("instance activated")

  def deactivate(self):
    self.isRunning = False
    print("instance deactivated")

  def __updateMouth(self):
    while self.isRunning:
        if self.mouth.to == 'open' and self.mouth.state != 'open':
            self.mouth.open()
        elif self.mouth.to =='closed' and self.mouth.state != 'closed':
            self.mouth.close()

print("program started")

bear = Bear()

# properly handle SIGINT (ctrl-c)
def sigint_handler(signal, frame):    
  bear.deactivate()
  sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)

bear.activate()

bear.mouth.to = 'open'
time.sleep(2)
bear.mouth.to = 'closed'
time.sleep(2)

bear.deactivate()
print("program ended")