#!/usr/bin/env python
import pyglet

print("trying to play test file")
baleeted = pyglet.media.load('public/sounds/baleeted.wav', streaming=False)
baleeted.play()

sys.exit(1)