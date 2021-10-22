#!/usr/bin/env python

from aiohttp import web
from time import sleep
import logging, socket, socketio, time

class WebServer:
  def __init__(self,bear):

    self.ip = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

    ## creates a new Async Socket IO Server
    sio = socketio.AsyncServer()
    
    ## Creates a new Aiohttp Web Application
    app = web.Application()

    # Binds our Socket.IO server to our Web App
    ## instance
    sio.attach(app)

    ## we can define aiohttp endpoints just as we normally
    ## would with no change
    async def index(request):
      with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

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
      await sio.emit('speaking_done')

    @sio.on('fetch_phrases')
    async def fetch_phrases(sid):
      await sio.emit('phrases_fetched', bear.phrases)

    ## We bind our aiohttp endpoint to our app
    ## router
    app.router.add_get('/', index)

    ## add static file route
    app.router.add_static('/public', 'public')

    self.app = app

  def start(self):
    print( "-------- ʕ•ᴥ•ʔ ---------")
    print( " RasPi Ruxpin is ONLINE ")
    print( "http://{}:8080".format(str(self.ip)))
    print( "--------------------------")
    print( "press ctrl-C to stop (might take a couple tries)")
    web.run_app(self.app, print=None, access_log=None)