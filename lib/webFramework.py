#!/usr/bin/env python
# based on Chippy Ruxpin by Next Thing Co 2015

from bottle import run, get, post, request, response, route, redirect, template, static_file
import socket

class WebFramework:
    def __init__(self,talkFunc, phraseFunc):
        self.ip = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
        print( "---------")
        print( "RasPi Ruxpin in ONLINE!")
        print( "In your browser, go to " + str(self.ip) + ":8080")
        print( "---------")
        self.talkFunc = talkFunc
        self.phraseFunc = phraseFunc

        @get('/public/<filename>')
        def server_static(filename):
            return static_file(filename, root='./public')
        
        @get('/naughty')
        def index():
            return template('naughty')

        @post('/naughty')
        def speak():
            phrase = request.forms.get('phrase')
            speech = request.forms.get('speech')

            if(phrase != ""):
                self.phraseFunc( phrase )
            else:
                self.talkFunc( speech )
            redirect('/naughty')

        @post('/slack')
        def slack():
            phrases = {
                "ants": "Archer: You want ants...",
                "believeitornot": "doggo: believe it or not...",
                "dogofwisdom": "doggo: ba daba da ba",
                "merryxmas": "clark: boss rant",
                "grownman": "airplane: grown man naked",
                "gymnasium": "airplane: hang around the gymnasium",
                "gladiators": "airplane: movies about gladiators",
                "turkish": "airplane: turkish prison",
                "surely": "airplane: don't call me surely",
                "88miles": "doc: if my calculations are correct...",
                "dumber": "harry: just when I think...",
                "nerfherder": "leia: why you stuck up...",
                "breath": "vader: breathing",
                "failed": "vader: you have failed me for the last time",
                "father": "vader: No, I am your father",
                "forceiswithyou": "vader: The force is with you...",
                "chewie": "chewie: grawgrhghghg...",
                "trynot": "yoda: Try not...",
                "everyone": "billy madison: everyone is now dumber",
                "hiney": "billy madison: so hot, want to touch the hiney",
                "bleep": "happy gilmore: *bleep*",
                "gohome": "happy gilmore: are you too good for your home?",
                "jackass": "happy gilmore: you suck, ya jackass",
                "kickmyownass": "happy gilmore: .. I'd have to kick my own ass",
                "piecesofshit": "happy gilmore: I eat pieces of shit like you...",
                "priceiswrong": "happy gilmore: the price is wrong",
                "shutthehellup": "happy gilmore: nice glass of shut the hell up",
                "taparoo": "happy gilmore: give it a tappy",
                "purpose": "rick and morty: what is my purpose? oh my god.",
                "assholomio": "ace ventura: assholomio, oh sodomia",
                "donotgointhere": "ace ventura: do NOT go in there... whew!",
                "fart": "monty python: I fart in your general direction",
                "ni": "monty python: we are the nights who say... ni!",
                "taunt": "monty python: Now go away or I shall taunt you a second time.",
                "hamster": "monty python: Your mother was a hamster...",
                "takedrugs": "caddyshack: Do you take drugs Danny?",
                "getnothing": "caddyshack: you'll get nothing and like it",
                "billybaroo": "caddyshack: billy baroo",
                "cinderella": "caddyshack: cinderalla scene",
                "bowlofsoup": "caddyshack: free bowl of soup",
                "whatthecrap": "strong bad: what the crap were you doing",
                "heystupid": "homestar: hey stupid",
                "canubelieveit": "homestar: can you believe it?",
                "baleeted": "homestar: baleeted",
            }
            text = request.forms.get('text')

            response.content_type = 'text/plain'

            if(text == "list"):
                phraseList = "```\n"
                for key, value in phrases.items():
                    phrase = ("%s => %s \n" % (key, value))
                    phraseList += phrase
                phraseList += "```\n"
                return phraseList
            else:
                if(text in phrases):
                    self.phraseFunc( text )
                    return "Chippy played the phrase: \"%s\"" % phrases[text]
                else:
                    self.talkFunc( text )
                    return "Chippy said: \"%s\"" % text

        @get('/')
        def index():
            return template('index')

        @post('/')
        def speak():
            redirect('/')

        run(host=self.ip, port=8080, debug=True)
