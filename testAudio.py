#!/usr/bin/env python
import sys
from lib.audioPlayer import AudioPlayer

audio = AudioPlayer()

audio.setVolume(100)

print("trying to play test file")
filename = "baleeted"
audio.play("public/sounds/"+filename+".wav")

sys.exit(1)
