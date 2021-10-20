#!/usr/bin/env python

try:
  import alsaaudio as aa
except ImportError:
  aa = None
import audioop
import pyaudio
import wave

class AudioPlayer:
  def __init__(self):
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

  def play(self,filename, bear):
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
      self.generateMouthSignal(rms, bear)

    # Close and terminate the stream
    stream.close()
    p.terminate()

  def generateMouthSignal(self,val, bear):
    #normalize value (anything less than 50 is essentially silence)
    if val<=100: val = 0

    delta = val - self.prevAudiovalue
    
    #if delta is positive, volume is increasing, open mouth
    if( delta > 0 ):
      self.mouthValue = 1
      bear.mouth.to = 'open'
    #if delta is negative, volume is decreasing, close mouth
    elif( delta < 0 ):
      self.mouthValue = 0
      bear.mouth.to = 'closed'
    
    self.prevAudiovalue = val

    print("val:{}, prevAudiovalue:{}, delta:{}, mouthValue:{}\n".format(val, self.prevAudiovalue, delta, self.mouthValue))
