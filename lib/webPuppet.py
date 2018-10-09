#!/usr/bin/env python

from bottle import run, get, post, request, response, route, redirect, template, static_file
import socket

class WebPuppet:
  def __init__(self,mouthFunc, eyesFunc):

    self.ip = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
    print( "---------")
    print( "RasPi Ruxpin in ONLINE! (puppet mode)")
    print( "In your browser, go to http://" + str(self.ip) + ":8080")
    print( "---------")

    self.mouthFunc = mouthFunc
    self.eyesFunc = eyesFunc

    @get('/public/<filename>')
    def server_static(filename):
      return static_file(filename, root='./public')
    
    @get('/')
    def index():
      return template('templates/puppet')

    @post('/')
    def puppet():
      part = request.forms.get('part')
      direction = request.forms.get('direction')

      if(part == 'mouth'):
        self.mouthFunc(direction=="open")
      elif(part=='eyes'):
        self.eyesFunc(direction=="open")
      redirect('/')

    run(host=self.ip, port=8080, debug=True)
