#!/usr/bin/env python
import sys
import argparse
import ConfigParser
import json
import os
import time

parser = argparse.ArgumentParser(description='testing open/close of bear motors')
parser.add_argument("-e", "--eyes", choices=["open", "close", "o", "c"], help="position of eyes")
parser.add_argument("-m", "--mouth", choices=["open", "close", "o", "c"], help="position of mouth")
args = parser.parse_args()

eyes = 'o' if args.eyes in ["open", "o"] else 'c'
mouth = 'o' if args.mouth in ["open", "o"] else 'c'

IS_PI = os.uname()[4][:3] == 'arm'

if(IS_PI):
  from lib.audioPlayer import AudioPlayer
  from lib.bear import Bear

# init audio player & bear
bear = Bear(config, None)

data = { "bear": {"eyes": {"open":(eyes == 'o')}, "mouth":{"open":(mouth == 'o')}}}
print(data)
bear.update(data)