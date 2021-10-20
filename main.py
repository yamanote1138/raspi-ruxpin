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
  # sort phrases alphabetically by key
  config.phrases = dict(sorted(phrases.items(), key = lambda kv:(kv[1], kv[0])))

# init audio player & bear
audio = AudioPlayer()
bear = Bear(config, audio)

# properly handle SIGINT (ctrl-c)
def sigint_handler(signal, frame):    
  bear.deactivate()
  sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)

# init web framework
try:
  bear.activate()
  web = WebFramework(bear)
  web.start()
except KeyboardInterrupt:
  bear.deactivate()
  sys.exit(0)

bear.deactivate()
sys.exit(1)
