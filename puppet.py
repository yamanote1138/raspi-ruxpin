#!/usr/bin/python

import sys
import time
import ConfigParser
import RPi.GPIO as GPIO

from lib.bear import Bear
from lib.webPuppet import WebPuppet

# read main config file
config = ConfigParser.RawConfigParser()
config.read('main.cfg')

bear = Bear(config)
web = WebPuppet(bear)

sys.exit(1)
