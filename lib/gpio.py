#!/usr/bin/env python
# based on Chippy Ruxpin by Next Thing Co 2015
# This sets the state of various GPIO pins (408 through 415)

import os
import time
import subprocess
from threading import Thread

class GPIO:
    def __init__(self):
        self.pins = []
        
    def setup(self,pin):
        cmd = "echo " + str(pin) + " > /sys/class/gpio/export"
        subprocess.call(cmd,shell=True, stdout=subprocess.PIPE)
        cmd = "echo \"out\" > /sys/class/gpio/gpio" + str(pin) + "/direction" 
        subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE)
        self.pins.append([pin,0,0])
        self.set( pin, 0 )
        
    def set(self,pin, val):
        if ( self.pins != None ):
            for pinObject in self.pins:
                if(pinObject[0]==pin and pinObject[1]!=val):
                    pinObject[1]=val
                    cmd = "echo " + str(val) + " > /sys/class/gpio/gpio" + str(pinObject[0]) + "/value"
                    subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE)
        
    def cleanup(self):
        for pinObject in self.pins:
            cmd = "echo 0 > /sys/class/gpio/gpio" + str(pinObject[0]) + "/value"
            subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE)
            cmd = "echo " + str(pinObject[0]) + " > /sys/class/gpio/unexport"
            subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE)
            self.pins = None
