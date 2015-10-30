# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import OlympusAir
import os
import datetime
import requests


from OlympusAir import OlympusAir, OlympusAirError, OlympusAirLiveViewFrame



cam = OlympusAir()
cam.commInterface()

cam.switchMode('standalone')
cam.switchMode('play')  
cam.switchMode('playmaintenance')  

cam.removeFileProtection()
cam.removeAllFiles()



cam.disconnect()



