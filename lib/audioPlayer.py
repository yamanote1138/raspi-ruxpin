import audioop, logging, platform, subprocess, wave
from time import sleep

# only import alsaaudio if not running on a mac
if platform.system() != 'Darwin':
  import alsaaudio as aa

class AudioPlayer:

  def __init__(self, config):
    self.prevAudiovalue = 0
    self.mouthValue = 0
    self.isPlaying = False
    self.mixer = config.get('audio', 'mixer')
    self.start_volume = config.getint('audio', 'start_volume')
    self.setVolume(self.start_volume)
    self.playData = None
    
  def setVolume(self, volume=75):
    # different implementation if running on a mac (facilitates local development)
    if platform.system() == 'Darwin':
      normalizedVolume = (volume*7)/100;
      logging.debug("set volume to {}%".format(volume));
      cmd = "set Volume {}".format(normalizedVolume)
      subprocess.run(['osascript', '-e', cmd]);
    elif aa is not None:
      # note: the sound output mixer needs to be set in config
      mx = aa.Mixer(self.mixer)
      mx.setvolume(volume)
      del mx
    else:
      logging.error("alsaaudio not installed, unable to set volume")

  def play(self,fileName):
    logging.info("playing file: {}".format(fileName))
    if platform.system() == 'Darwin':
      # alternate implementation if running on a mac (facilitates local development)
      # note: this does not engage mouth motor code at all, just plays the sound file
      subprocess.run(['afplay', fileName]);
    else:
      wavfile = wave.open(fileName,'r')
      chunk = 1024
      output = aa.PCM(aa.PCM_PLAYBACK, aa.PCM_NORMAL)
      output.setchannels(1)
      output.setrate(22050)
      output.setformat(aa.PCM_FORMAT_S16_LE)
      output.setperiodsize(chunk)

      data = wavfile.readframes(chunk)
      max_vol_factor =5000
      try:
        while data!='' and data is not None and data != b'':
          output.write(data)

          try:
            # check data segment to ensure it is a complete frame
            if((len(data) % chunk) == 0):
              # Split channel data and find maximum volume
              # channel_l=audioop.tomono(data, 2, 1.0, 0.0)
              channel_r=audioop.tomono(data, 2, 0.0, 1.0)
              # max_l = audioop.max(channel_l,2)/max_vol_factor
              max_r = audioop.max(channel_r,2)//max_vol_factor

              for i in range (1,8):
                self.generateMouthSignal((1<<max_r)-1)
          except:
            logging.exception('')
            
          data = wavfile.readframes(chunk)
      except:
        logging.exception('')
      sleep( .25 )

  def generateMouthSignal(self,val):
    delta = val - self.prevAudiovalue 
    if( delta < -2 or val == 0 ):
      self.mouthValue = 0
    elif( delta > 0 ):
      self.mouthValue = 1

    self.prevAudiovalue = val