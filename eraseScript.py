# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import olympusair
import os
import datetime
import requests


cam = olympusair.Camera()
cam.commInterface()

cam.switchMode('standalone')
cam.switchMode('play')  
cam.switchMode('playmaintenance')  

cam.removeFileProtection()
cam.removeAllFiles()



cam.disconnect()



