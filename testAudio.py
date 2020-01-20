#!/usr/bin/env python
import sys
import os
from lib.audioPlayer import AudioPlayer

# init audio player and play test file
audio = AudioPlayer()
filename = "baleeted"
audio.play("public/sounds/"+filename+".wav")
