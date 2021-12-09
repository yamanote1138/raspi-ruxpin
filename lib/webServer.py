#!/usr/bin/env python

from aiohttp import web
import jinja2
import aiohttp_jinja2
import os, socket, socketio

class WebServer:
  def __init__(self,bear):

    self.ip = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

    ## creates a new Async Socket IO Server
    sio = socketio.AsyncServer()
    
    ## Creates a new Aiohttp Web Application
    app = web.Application()

    aiohttp_jinja2.setup(
      app, loader=jinja2.FileSystemLoader(os.path.join(os.getcwd(), "templates"))
    )

    # bind socketio server to web app instance
    sio.attach(app)

    @aiohttp_jinja2.template("index.html")
    async def index(request):
      return {'character':bear.character}

    # respond to client events
    @sio.on('update_bear')
    async def update_bear(sid, data):
      bear.update(data)
      await sio.emit('bear_updated', data)

    @sio.on('speak')
    async def speak(sid, phrase):
      if(phrase != ""): bear.say(phrase)
      await sio.emit('speaking_done')

    @sio.on('play')
    async def play(sid, filename):
      if(filename != ""): bear.play(filename)
      await sio.emit('playing_done')

    @sio.on('set_volume')
    async def volume(sid, level):
      if(level > 10 and level < 90): bear.audio.setVolume(level)
      await sio.emit('volume_set')

    @sio.on('fetch_phrases')
    async def fetch_phrases(sid):
      await sio.emit('phrases_fetched', bear.phrases)

    # bind aiohttp endpoint to app router
    app.router.add_get('/', index)

    # add route for static files
    app.router.add_static('/public', 'public')

    self.app = app

  def start(self):
    print( "-------- ʕ•ᴥ•ʔ ---------")
    print( " RasPi Ruxpin is ONLINE ")
    print( "http://{}:8080".format(str(self.ip)))
    print( "--------------------------")
    print( "press ctrl-C to stop (might take a couple tries)")
    web.run_app(self.app, print=None, access_log=None)