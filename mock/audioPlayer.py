import logging
from time import sleep

class AudioPlayer:

  def __init__(self):
    self.prevAudiovalue = 0
    self.mouthValue = 0
    self.setVolume(100)
    
  def setVolume(self, volume=75):
    logging.debug("volume set at {}").format(volume)

  def play(self,fileName):
    logging.debug("playing file: {}".format(fileName))
    sleep(2)
