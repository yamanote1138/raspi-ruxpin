import logging, subprocess
from time import sleep

class AudioPlayer:

  def __init__(self, config):
    self.prevAudiovalue = 0
    self.mouthValue = 0
    self.setVolume(100)
    
  def setVolume(self, volume=70):
    normalizedVolume = volume/10;
    cmd = "set Volume {}".format(normalizedVolume)
    subprocess.run([
      'osascript',
      '-e',
      cmd
    ]);
    logging.debug("volume set at {}".format(volume))

  def play(self,fileName):
    logging.debug("playing file: {}".format(fileName))
    subprocess.run([
      'afplay', 
      fileName
    ]);
