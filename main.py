#!/usr/bin/python

import configparser, json, logging, signal, sys
from lib.bear import Bear
from lib.webServer import WebServer

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# read main config file
config = configparser.RawConfigParser()
config.read('config/main.cfg')

# read phrases config file
with open('config/phrases.json', 'r') as f:
  phrases = json.load(f)
  # sort phrases alphabetically by key
  config.phrases = dict(sorted(phrases.items(), key = lambda kv:(kv[1], kv[0])))

# init bear
bear = Bear(config)

# properly handle SIGINT (ctrl-c)
def sigint_handler(signal, frame):    
  ws.app.shutdown()
  bear.deactivate()
  sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)

# init web framework
try:
  bear.activate()
  ws = WebServer(bear)
  ws.start()
except KeyboardInterrupt:
  bear.deactivate()
  sys.exit(0)

bear.deactivate()
sys.exit(1)
