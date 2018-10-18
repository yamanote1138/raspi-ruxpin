# Raspi Ruxpin!

Make a creepy old Teddy Ruxpin say whatever you want!

Entering text through the web interface will make Teddy Ruxpin say whatever you want with syncronized mouth movements.

## Introduction

This project was originally based on the [version](https://www.hackster.io/chip/c-h-i-p-py-ruxpin-5f02f1) constructed by the nice folks at NextThing, inc. Unfortunately, it appears as though they and their nifty $9 CHIP have both disappeared into the ether.

So, on that note, I've ported and rebuilt the project for use with a Raspberry Pi.


## What You'll Need
(todo)

## Wiring
![Fritzing](fritzing.png)

## Installation

Make sure you install the following dependencies:

```sh
sudo apt-get install python-setuptools python-dev build-essential espeak alsa-utils
sudo apt-get install python-alsaaudio python-numpy python-twitter python-bottle mplayer
```

## Configuration
To start the application, run this script:

## Operation
To start the application, run this script:

```sh
sudo python chippyRuxpin.py
```

Assuming your RasPi is connected to WIFI or ethernet, you should see a message that looks similar to this:

```sh
---------
RASPI RUXPIN IS ONLINE!
In your browser, go to http://[ipaddress]:8080
---------
```

