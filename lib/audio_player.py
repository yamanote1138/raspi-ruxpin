import audioop
import logging
import platform
import subprocess
import wave
from time import sleep

from lib.direction import Direction

# only import alsaaudio if not running on a mac
if platform.system() != 'Darwin':
  import alsaaudio as aa

class AudioPlayer:
  """audio utilities explicitly for use with this talking bear project

  Attributes:
    flight_speed     The maximum speed that such a bird can attain.
    nesting_grounds  The locale where these birds congregate to reproduce.
  """

  def __init__(self, config):
    self.mouth_direction = Direction.BRAKE
    self.__mixer = config.get('audio', 'mixer')
    self.set_volume(config.getint('audio', 'start_volume'))

  def set_volume(self, volume=75):
    """sets the system volume

    Args:
      volume (int, optional): desired volume level (scale of 0 to 100, defaults to 75)
    """
    logging.debug("setting volume to %i", volume)
    if platform.system() == 'Darwin':
      # different implementation if running on a mac (facilitates local development)
      subprocess.run(['osascript', '-e', f"set Volume {(volume*7)/100}"], check=True)
    elif aa is not None:
      # note: the sound output mixer needs to be set in config
      aa.Mixer(self.__mixer).setvolume(volume)
    else:
      logging.error("alsaaudio not installed, unable to set volume")

  def play(self, audio_file_name):
    """play audio file

    Args:
        audio_file_name ([type]): [description]
    """
    logging.info("playing file: %s", audio_file_name)
    if platform.system() == 'Darwin':
      # alternate implementation if running on a mac (facilitates local development)
      # note: this does not engage mouth motor code at all, just plays the sound file
      subprocess.run(['afplay', audio_file_name], check=True)
    else:
      wavfile = wave.open(audio_file_name, 'r')
      chunk = 1024
      output = aa.PCM(aa.PCM_PLAYBACK, aa.PCM_NORMAL)
      output.setchannels(1)
      output.setrate(22050)
      output.setformat(aa.PCM_FORMAT_S16_LE)
      output.setperiodsize(chunk)

      max_vol_factor =5000
      prev_val = 0

      data = wavfile.readframes(chunk)

      while data!='' and data is not None and data != b'':
        try:
          output.write(data)

          # check data segment to ensure it is a complete frame
          if len(data) % chunk == 0:
            # Split channel data and find maximum volume
            # channel_l=audioop.tomono(data, 2, 1.0, 0.0)
            channel_r=audioop.tomono(data, 2, 0.0, 1.0)
            # max_l = audioop.max(channel_l,2)/max_vol_factor
            max_r = audioop.max(channel_r,2)//max_vol_factor

            for i in range (1,8):
              val = (1<<max_r)-1
              self.mouth_direction = __get_mouth_direction(val, prev_val)
              prev_val = val

          data = wavfile.readframes(chunk)
        except:
          logging.exception('')
      sleep( .25 )

def __get_mouth_direction(self, val, prev_val):
  """[summary]

  Args:
    val ([type]): [description]
  """
  delta = val - prev_val
  if delta < 0 or val == 0:
    return Direction.CLOSING
  return Direction.OPENING
