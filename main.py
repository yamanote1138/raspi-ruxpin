#!/usr/bin/python
# based on Chippy Ruxpin by Next Thing Co

import sys
import ConfigParser
import json
import os

IS_PI = os.uname()[4][:3] == 'arm'

if(IS_PI):
  from lib.audioPlayer import AudioPlayer
  from lib.bear import Bear
else:
  from lib.mockAudioPlayer import AudioPlayer
  from lib.mockBear import Bear

from lib.webFramework import WebFramework

# read main config file
config = ConfigParser.RawConfigParser()
config.read('main.cfg')

# read phrases config file
with open('phrases.json', 'r') as f:
  phrases = json.load(f)

# init audio player & bear
audio = AudioPlayer()
bear = Bear(config, audio)

# init web framework
web = WebFramework(bear, phrases)
sys.exit(1)
