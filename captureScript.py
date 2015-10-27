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

os.mkdir(dirPath)

cam.startPreview()

for i in range(10):
    
    cam.setProperty('FOCUS_STILL','FOCUS_SAF')
    
    attempts = 0
    while attempts < 10:
        try:
            cam.takePicture()
            
            break
        except requests.exceptions.HTTPError as err:
            # leave the script ?
            # Recreate camera object?
            pass
        except OlympusAirError as err:
            if err.value == OlympusAirError.AF:
                print 'Autofocus error'
                cam.setProperty('FOCUS_STILL','FOCUS_MF')
        
        attempts = attempts + 1


cam.waitOnCardWrite()	


cam.stopPreview()

for i in range(10):
	jpeg, raw = cam.getLatestFile(i)
    
        jpegFile = open(dirPath + '/' + 'LED%02i.jpg' % (9 - i),'w')
        jpegFile.write(jpeg)
    
        rawFile = open(dirPath + '/' + 'LED%02i.orf' % (9 - i),'w')
        rawFile.write(jpeg)
  
# What if we tried enough times
    


cam.disconnect()



