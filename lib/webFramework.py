#!/usr/bin/env python
# based on Chippy Ruxpin by Next Thing Co 2015

from bottle import run, get, post, request, response, route, redirect, template, static_file
import socket

class WebFramework:
  def __init__(self,bear,phrasesDict):
    self.ip = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
    print( "---------")
    print( "RasPi Ruxpin in ONLINE!")
    print( "In your browser, go to http://" + str(self.ip) + ":8080")
    print( "---------")
    self.talkFunc = talkFunc
    self.phraseFunc = phraseFunc

    @get('/public/<filename>')
    def server_static(filename):
      return static_file(filename, root='./public')
      
    @get('/')
    def index():
      return template('templates/index', phrases=phrasesDict)

    @get('/puppet')
    def index():
      e = request.query.e or 'o'
      m = request.query.m or 'o'

      if(bear!=None):
        if(e == 'o'):
          self.bear.eyes.open()
        else:
          self.bear.eyes.close()
        if(m == 'o'):
          self.bear.mouth.open()
        else:
          self.bear.mouth.close()
      else:
        print(('open' if e =='o' else 'close') + ' eyes')
        print(('open' if m =='o' else 'close') + ' mouth')

      return template('templates/puppet', e=e, m=m)

    @post('/phrase')
    def phrase():
      filename = request.forms.get('phrase')

      if(filename != ""):
        if(self.bear!=None) self.bear.phrase( filename )
      redirect('/')

    @post('/speak')
    def speak():
      text = request.forms.get('speech')

      if(text != ""):
        if(self.bear!=None) self.bear.talk( text )
      redirect('/')

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
          if(self.bear!=None) self.bear.phrase( text )
          return "RasPi Ruxpin played the phrase: \"%s\"" % phrasesDict[text]
        else:
          if(self.bear!=None) self.bear.talk( text )
          return "Raspi Ruxpin said: \"%s\"" % text

    run(host=self.ip, port=8080, debug=True)
