#!/usr/bin/env python
# based on Chippy Ruxpin by Next Thing Co 2015

from bottle import run, get, post, request, response, route, redirect, template, static_file
import socket

class WebFramework:
  def __init__(self,bear):
    # self.ip = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
    self.ip = '127.0.0.1'
    self.e = 'o'
    self.m = 'c'

    print( "---------")
    print( "RasPi Ruxpin in ONLINE!")
    print( "In your browser, go to http://" + str(self.ip) + ":8080")
    print( "---------")

    @get('/public/<path:path>')
    def server_static(path):
      return static_file(path, root='./public')
      
    @get('/')
    def index():
      return template('templates/index', phrases=bear.phrases, e=self.e, m=self.m)

    @get('/api/bear')
    def apiBearGetStatus():
      return bear.getStatus()

    @get('/api/bear/<servo>/<action>')
    def apiBearServoAction(servo, action):
      data = { "bear": {servo: {"open":(action == 'open')}}}
      return bear.update(data)

    @post('/api/bear')
    def apiBearPostStatus():
      data = request.json
      return bear.update(data)

    @get('/puppet')
    def puppet():
      self.e = request.query.e or 'o'
      self.m = request.query.m or 'o'

      data = { "bear": {"eyes": {"open":(self.e == 'o')}, "mouth":{"open":(self.m == 'o')}}}
      print(data)
      bear.update(data)
      return index()

    @post('/api/play/<filename>')
    def play(filename):
      bear.play(filename)
      return index()

    @post('/speak')
    def speak():
      text = request.forms.get('speech')
      if(text != ""): bear.talk(text)
      return index()

    @post('/slack')
    def slack():
      text = request.forms.get('text')
      response.content_type = 'text/plain'

      if(text == "list"):
        phraseList = "```\n"
        for key, value in bear.phrases.items():
          phrase = ("%s => %s \n" % (key, value))
          phraseList += phrase
          phraseList += "```\n"
          return phraseList
      else:
        if(text in bear.phrases):
          bear.phrase( text )
          return "RasPi Ruxpin played the phrase: \"%s\"" % phrases[text]
        else:
          bear.talk( text )
          return "RasPi Ruxpin said: \"%s\"" % text

    run(host=self.ip, port=8080, debug=True)
