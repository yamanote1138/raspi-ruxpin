#!/usr/bin/env python
import sys
import ConfigParser
import json
import time

from lib.audioPlayer import AudioPlayer
from lib.bear import Bear

# read main config file
config = ConfigParser.RawConfigParser()
config.read('config/main.cfg')

# read phrases config file
with open('config/phrases.json', 'r') as f:
  phrases = json.load(f)
  config.phrases = phrases

# init audio player & bear
audio = AudioPlayer()
bear = Bear(config, audio)

# bear.eyes.blink()
# time.sleep(1)
# bear.mouth.blink()

# bear.play("88miles")

bear.say("I have seen roadkill with better taste")

# should give process time to finish
raw_input("Press Enter to quit...")

# sys.exit(1)