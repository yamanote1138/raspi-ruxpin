#!/usr/bin/env python
# based on Chippy Ruxpin by Next Thing Co 2015

from bottle import run, get, post, request, response, route, redirect, template, static_file
import socket

class WebFramework:
  def __init__(self,bear,phrasesDict):
    self.ip = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
    self.e = 'o'
    self.m = 'c'

    print( "---------")
    print( "RasPi Ruxpin in ONLINE!")
    print( "In your browser, go to http://" + str(self.ip) + ":8080")
    print( "---------")

    @get('/public/<filename>')
    def server_static(filename):
      return static_file(filename, root='./public')
      
    @get('/')
    def index():
      return template('templates/index', phrases=phrasesDict, e=self.e, m=self.m)

    @get('/api/bear')
    def apiBearGetStatus():
      return { "bear": { "eyes": { "open": bear.eyes.open }, "mouth": { "open": bear.mouth.open } } }

    @post('/api/bear')
    def apiBearPostStatus():
      data = request.json
      bear.update(data)
      return apiBearGetStatus()



    @get('/puppet')
    def puppet():
      self.e = request.query.e or 'o'
      self.m = request.query.m or 'o'

      if(self.e == 'o'):
        bear.eyes.open()
        self.e == 'c'
      else:
        bear.eyes.close()
      if(self.m == 'o'):
        bear.mouth.open()
      else:
        self.m == 'c'
        bear.mouth.close()
      return index()

    @post('/phrase')
    def phrase():
      filename = request.forms.get('filename')
      if(filename != ""): bear.phrase( filename )
      return index()

    @post('/speak')
    def speak():
      text = request.forms.get('speech')
      if(text != ""): bear.talk( text )
      return index()

    @post('/slack')
    def slack():
      text = request.forms.get('text')
      response.content_type = 'text/plain'

      if(text == "list"):
        phraseList = "```\n"
        for key, value in phrasesDict.items():
          phrase = ("%s => %s \n" % (key, value))
          phraseList += phrase
          phraseList += "```\n"
          return phraseList
      else:
        if(text in phrasesDict):
          bear.phrase( text )
          return "RasPi Ruxpin played the phrase: \"%s\"" % phrasesDict[text]
        else:
          bear.talk( text )
          return "Raspi Ruxpin said: \"%s\"" % text

    run(host=self.ip, port=8080, debug=True)
