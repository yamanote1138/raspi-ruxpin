# Chippy Ruxpin!

A project for driving mouth and eye motors for an old Teddy Ruxpin with text-to-speech capabilities through a web interface.
Entering text through the web interface will make Teddy Ruxpin say whatever you want with syncronized mouth movements.
All done with CHIP, the world's first $9 computer.

Make sure you install the following dependencies:

```sh
sudo apt-get install python-setuptools python-dev build-essential espeak alsa-utils
sudo apt-get install python-alsaaudio python-numpy python-twitter python-bottle mplayer
```
To start the application, run this script:

```sh
sudo python chippyRuxpin.py
```

Assuming your CHIP is connected to WIFI or ethernet, you should see a message that looks similar to this:

```sh
---------
CHIPPY RUXPIN IS ONLINE!
In your browser, go to http://10.1.2.52:8080
---------
```

Simply go to that URL in your browser and you should see a webpage with a text input box. Here, you can make Chippy Ruxpin say whatever you want.
You can also have him read tweets from Twitter if you like.

NOTE: To properly associate your Twitter account with this code, please take edit the following file:

```sh
chippyRuxpin.py
```

At the top, you should see these variables:

```sh
consumerKey='INSERT YOUR CONSUMER KEY HERE FROM TWITTER'
consumerSecret='INSERT YOUR CONSUMER SECRET HERE FROM TWITTER'
accessTokenKey='INSERT YOUR ACCESS TOKEN KEY HERE FROM TWITTER'
accessTokenSecret='INSERT YOUR ACCESS TOKEN SECRET HERE FROM TWITTER'
```

You need to change these values with the proper keys associated with your own Twitter account. To generate these keys, go to the following URL:

https://dev.twitter.com/oauth/overview/application-owner-access-tokens