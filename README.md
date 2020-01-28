# Raspi Ruxpin!

Make a creepy old Teddy Ruxpin say whatever you want!

Entering text through the web interface will make Teddy Ruxpin say whatever you want with syncronized mouth movements.

## Introduction

This project was originally based on the [version](https://www.hackster.io/chip/c-h-i-p-py-ruxpin-5f02f1) constructed by the nice folks at NextThing, inc. Unfortunately, it appears as though they and their nifty $9 CHIP have both disappeared into the ether.

So, on that note, I've ported and rebuilt the project for use with a Raspberry Pi.


## What You'll Need
- Teddy Ruxpin
- RaspberryPi 3 (probably works on earlier versions, but unverified)
- Breadboard
- jumpers
- Sparkfun TB6612FNG H-Bridge Breakout

## Wiring
![Fritzing](fritzing.png)

## Installation

Make sure you install the following dependencies:

```sh
sudo apt-get install python-setuptools python-dev build-essential espeak alsa-utils
sudo apt-get install python-alsaaudio python-numpy python-bottle mplayer
```

## Configuration
make a copy of the default config and name it `main.cfg`
```sh
cp main.cfg.default main.cfg
```

using whatver editor tickles your fancy, set the GPIO pins to whatever you'd like
NOTE: the default config maps to the GPIO pins as wired in the attached fritzing diagram

## Operation
To start the application, run this script:

```sh
sudo python main.py
```

Assuming your RasPi is connected to WIFI or ethernet, you should see a message that looks similar to this:

```sh
---------
RASPI RUXPIN IS ONLINE!
In your browser, go to http://[ipaddress]:8080
---------
```

## Mac Local Dev notes
`brew install pyenv`
`pyenv install 2.7.13`
`brew install portaudio`
`pip install ConfigParser`
`pip install pyaudio`

