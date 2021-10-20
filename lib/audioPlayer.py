import alsaaudio as aa
import audioop
from time import sleep
import struct
import math
import array
import numpy as np
import wave
import os
import subprocess
import logging

class AudioPlayer:

  def __init__(self):
    subprocess.Popen('amixer cset numid=1 100%' ,shell=True, stdout=subprocess.PIPE ) # Set PA mixer volume to 100%
    subprocess.Popen('amixer cset numid=2 2' ,shell=True, stdout=subprocess.PIPE ) # Set right mixer to be "right" (2)
    subprocess.Popen('amixer cset numid=3 1' ,shell=True, stdout=subprocess.PIPE ) # Set left mixer to be "left" (1)
    subprocess.Popen('amixer cset numid=4 1' ,shell=True, stdout=subprocess.PIPE ) # Set DAC self.output to be "Direct" (2... or 1 for "Mixed" if you prefer)
    self.prevAudiovalue = 0
    self.mouthValue = 0
    self.setVolume(100)
    
  def setVolume(self, volume=75):
    if aa is not None:
      mixer = aa.Mixer('PCM')
      mixer.setvolume(volume)
      current_volume = mixer.getvolume() # Get the current Volume
      print("volume set at {}").format(current_volume)
    else:
      print("alsaaudio not installed, unable to set volume")

  def play(self,fileName):

    print("playing file: {}".format(fileName))

    # Initialise matrix
    matrix=[0,0,0,0,0,0,0,0]

    # Set up audio
    wavfile = wave.open(fileName,'r')
    chunk = 1024
    output = aa.PCM(aa.PCM_PLAYBACK, aa.PCM_NORMAL)
    output.setchannels(1)
    output.setrate(16000)
    # output.setrate(22050)
    output.setformat(aa.PCM_FORMAT_S16_LE)
    output.setperiodsize(chunk)

    data = wavfile.readframes(chunk)
    max_vol_factor =5000
    try:
      while data!='':
        output.write(data)

        try:
          # Split channel data and find maximum volume
          # channel_l=audioop.tomono(data, 2, 1.0, 0.0)
          channel_r=audioop.tomono(data, 2, 0.0, 1.0)
          # max_l = audioop.max(channel_l,2)/max_vol_factor
          max_r = audioop.max(channel_r,2)/max_vol_factor

          for i in range (1,8):
            self.generateMouthSignal((1<<max_r)-1)
        except:
          logging.exception('')
          
        data = wavfile.readframes(chunk)
    except:
      logging.exception('')
      data = None
      
    os.system( '/etc/init.d/alsa-utils restart' )
    sleep( .25 )

  def generateMouthSignal(self,val):
    delta = val - self.prevAudiovalue 
    if( delta < -2 or val == 0 ):
      self.mouthValue = 0
    elif( delta > 0 ):
      self.mouthValue = 1

    self.prevAudiovalue = val