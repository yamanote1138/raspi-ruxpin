#!/usr/bin/env python

class AudioPlayer:
  def __init__(self):
    self.prevAudiovalue = 0
    self.mouthValue = 0
    self.setVolume(100)

  def setVolume(self, volume=75):
    print("volume set at {}").format(volume)

  def play(self,filename):
    print("played {}").format(filename)

  def generateMouthSignal(self,val):
    delta = val - self.prevAudiovalue 
    if( delta < -2 or val == 0 ):
      self.mouthValue = 0
    elif( delta > 0 ):
      self.mouthValue = 1
      self.prevAudiovalue = val

    print(self.mouthValue)
