#!/usr/bin/env python

import alsaaudio as aa
import audioop
import pyaudio
import wave

class AudioPlayer:
  def __init__(self):
    self.prevAudiovalue = 0
    self.mouthValue = 0
    self.setVolume(100)

  def setVolume(self, volume=75):
    mixer = aa.Mixer('PCM')
    mixer.setvolume(volume)
    current_volume = mixer.getvolume() # Get the current Volume
    print("volume set at {}").format(current_volume)

  def play(self,filename):
    # Set chunk size of 1024 samples per data frame
    chunk = 1024  

    # Create an interface to PortAudio
    p = pyaudio.PyAudio()

    # Open the sound file 
    wf = wave.open(filename, 'rb')

    # Open a .Stream object to write the WAV file to
    # 'output = True' indicates that the sound will be played rather than recorded
    stream = p.open(
      format = p.get_format_from_width(wf.getsampwidth()),
      channels = wf.getnchannels(),
      rate = wf.getframerate(),
      output = True
    )

    # Read data in chunks
    data = wf.readframes(chunk)

    # Play the sound by writing the audio data to the stream
    while data != '':
      stream.write(data)
      data = wf.readframes(chunk)
      rms = audioop.rms(data, 2)
      self.generateMouthSignal(rms)

    # Close and terminate the stream
    stream.close()
    p.terminate()

  def generateMouthSignal(self,val):
    delta = val - self.prevAudiovalue 
    if( delta < -2 or val == 0 ):
      self.mouthValue = 0
    elif( delta > 0 ):
      self.mouthValue = 1
      self.prevAudiovalue = val

    # print(self.mouthValue)