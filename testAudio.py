#!/usr/bin/env python
from lib.audioPlayer import AudioPlayer

audio = AudioPlayer()
filename = "public/sounds/baleeted.wav"

print("trying to play test file")
audio.play("public/sounds/"+filename+".wav")

sys.exit(1)