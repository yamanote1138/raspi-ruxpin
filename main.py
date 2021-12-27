import argparse
import configparser
import json
import logging
import signal
import sys

from lib.bear import Bear
from lib.webServer import WebServer

parser = argparse.ArgumentParser()
parser.add_argument(
  '-log',
  '--loglevel',
  default='info',
  help='Provide logging level. Example --loglevel debug, default=warning'
)
args = parser.parse_args()

logging.basicConfig(level=args.loglevel.upper() )
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

# init web framework
ws = WebServer(bear)

# properly handle SIGINT (ctrl-c)
def signal_handler(signal, frame):
  raise KeyboardInterrupt

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
  bear.activate()
  ws.start()
except KeyboardInterrupt:
  pass
finally:
  bear.deactivate()
  sys.exit(0)
