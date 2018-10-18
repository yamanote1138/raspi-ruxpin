#!/usr/bin/python
# based on Chippy Ruxpin by Next Thing Co

import sys
import ConfigParser
import json

from lib.audioPlayer import AudioPlayer
from lib.webFramework import WebFramework
from lib.bear import Bear

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
