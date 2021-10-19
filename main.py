#!/usr/bin/python

import sys, ConfigParser, json, os, signal, time

from lib.audioPlayer import AudioPlayer
from lib.bear import Bear
from lib.webFramework import WebFramework

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

# init web framework
web = WebFramework(bear)

bear.activate()
time.sleep(1)
web.start()

# properly handle SIGINT (ctrl-c)
def sigint_handler(signal, frame):    
  bear.deactivate()
  sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)

bear.deactivate()
sys.exit(1)
