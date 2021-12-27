import logging
from os import times
import random
import subprocess
import time

from time import sleep
from threading import Thread
from lib.direction import Direction
from lib.state import State

from lib.servo import Servo
from lib.audio_player import AudioPlayer
from lib.pin_set import PinSet

class Bear:
  """[summary]
  """
  def __init__(self, config):
    self.is_running = True
    self.is_talking = False

    # attach audio player
    self.audio = AudioPlayer(config)

    # add list of supported phrases
    self.phrases = config.phrases

    # bind mouth and eye servos based on pins defined in config
    self.servos = {
      "eyes": Servo(
        PinSet(
          config.getint('pins', 'pwma'),
          config.getint('pins', 'ain1'),
          config.getint('pins', 'ain2')
        ),
        duration=config.getfloat('settings', 'eyes_duration'),
        speed=config.getint('settings', 'eyes_speed'),
        label='eyes'
      ),
      "mouth": Servo(
        PinSet(
          config.getint('pins', 'pwmb'),
          config.getint('pins', 'bin1'),
          config.getint('pins', 'bin2')
        ),
        duration=config.getfloat('settings', 'mouth_duration'),
        speed=config.getint('settings', 'mouth_speed'),
        label='mouth'
      )
    }

    self.character = {
      'name': config.get('character', 'name'),
      'prefix': config.get('character', 'prefix')
    }
    logging.debug("character is: %s", self.character['name'])
    logging.debug("prefix is: %s", self.character['prefix'])

    self.talk_thread = Thread(target=self. __talk_monitor, daemon=True)
    self.blink_thread = Thread(target=self. __blink_monitor, daemon=True)
    logging.debug("bear constructor finished")

  def __del__(self):
    logging.debug("bear deconstructor finished")

  def activate(self):
    """open bear's eyes and setup talking and blinking threads"""
    logging.info("activating bear, please wait...")
    self.is_running = True

    self.servos["eyes"].open()

    self.talk_thread.start()
    self.blink_thread.start()
    logging.debug("bear instance activated")

  def deactivate(self):
    """put the bear to sleep: close eyes and mouth"""
    logging.info("deactivating bear, please wait...")

    self.is_running = False
    self.is_talking = False

    self.servos["eyes"].close()
    self.servos["mouth"].close()

    logging.debug("bear instance deactivated")

  def __talk_monitor(self):
    """move mouth when audio file is playing"""
    previous_direction = Direction.BRAKE
    timestamp = 0
    while self.is_running:
      if self.is_talking:
        if self.audio.mouth_direction != previous_direction:
          previous_direction = self.audio.mouth_direction
          timestamp = time.time()
          self.servos["mouth"].set_direction(self.audio.mouth_direction)
        else:
          if time.time() - timestamp > 0.4:
            self.servos["mouth"].set_direction(Direction.BRAKE)
        sleep(.02)
      else:
        sleep(.1)

  def __blink_monitor(self):
    """randomly blink eyes while bear is talking"""
    while self.is_running:
      if self.is_talking:
        sleep(random.randint(1,3))
        self.servos["eyes"].close()
        sleep(.2)
        self.servos["eyes"].open()
      else:
        sleep(.1)

  def update(self, data: dict):
    """update position of eyes and/or mouth

    Args:
        data dict: position settings
    """
    if self.is_talking:
      logging.error('cannot update bear while it is talking')
    else:
      for key in data:
        if data[key] == State.OPEN.value and self.servos[key].state != State.OPEN:
          self.servos[key].open()
        elif data[key] == State.CLOSED.value and self.servos[key].state != State.CLOSED:
          self.servos[key].close()

  def play(self, filename):
    """play a sound file with corresponding mouth movements and blinking

    Args:
        filename (str, required): path to wave file to play
    """
    self.is_talking = True
    self.servos["mouth"].set_direction(Direction.BRAKE)
    self.servos["mouth"].pwm.start(self.servos["mouth"].speed)
    try:
      if filename == 'espeak':
        self.audio.play("sounds/espeak.wav")
      else:
        self.audio.play(f"sounds/{filename}.wav")
    except:
      logging.exception("an error occurred while the bear was trying to talk")
      self.servos["mouth"].stop()
      self.servos["eyes"].stop()
    finally:
      self.is_talking = False
      self.servos["mouth"].stop()

  def say(self, text):
    """[summary]

    Args:
        text ([type]): [description]
    """
    subprocess.run(
      [
        "espeak",
        "-w","sounds/espeak.wav",
        "-s","125",
        "-v","en+m3",
        "-p","25",
        "-a","175",
        text
      ],
      check=True
    )
    logging.debug('espeak ran')
    self.play("espeak")
