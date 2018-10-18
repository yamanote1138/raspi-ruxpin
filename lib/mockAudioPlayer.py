#!/usr/bin/env python

class AudioPlayer:
  def __init__(self):
    print("AudioPlayer.init()")

  def play(self,fileName):
    print("AudioPlayer.play() : \"%s\"" % filename)

  def generateMouthSignal(self,val):
    print("AudioPlayer.generateMouthSignal() : \"%s\"" % val)
