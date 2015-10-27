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
cam.switchMode('rec')
cam.setProperty('FOCUS_STILL','FOCUS_SAF')
cam.setProperty('RAW','ON')
cam.setProperty('TAKE_DRIVE','DRIVE_NORMAL')
cam.setProperty('TAKEMODE','P')
cam.setProperty('DESTINATION_FILE','DESTINATION_FILE_MEDIA')
cam.setZoom(20)

 
dirPath = './' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
print '======= ' + dirPath + ' ======='

# os.mkdir(dirPath)

cam.startPreview()

try:
	
		
	frame = OlympusAirLiveViewFrame()
	frame.getLiveViewFrame(cam.lvSocket)

	fle =  open('liveView.jpg','w')
        fle.write(frame.jpegStream)

except: 
	cam.stopPreview()

    


cam.disconnect()



