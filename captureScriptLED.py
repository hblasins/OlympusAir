# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import OlympusAir
import os
import datetime
import requests

import RPi.GPIO as GPIO
from OlympusAir import OlympusAir, OlympusAirError, OlympusAirLiveViewFrame

# LEDpins = [17, 27, 22, 6, 13, 19, 26]
LEDpins = [19, 6, 26, 22, 27, 17, 13]
GPIO.setmode(GPIO.BCM)
GPIO.setup(LEDpins,GPIO.OUT)
GPIO.output(LEDpins, GPIO.LOW)

cam = OlympusAir()
cam.commInterface()
cam.switchMode('standalone')
cam.switchMode('rec')
cam.setProperty('FOCUS_STILL','FOCUS_SAF')
cam.setProperty('RAW','ON')
cam.setProperty('TAKE_DRIVE','DRIVE_NORMAL')
cam.setProperty('TAKEMODE','P')
cam.setProperty('DESTINATION_FILE','DESTINATION_FILE_MEDIA')
cam.setProperty('EXPREV','-1.0')

 
dirPath = './' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
print '======= ' + dirPath + ' ======='

os.mkdir(dirPath)

cam.startPreview()

for i in range(len(LEDpins)):
    
    cam.setProperty('FOCUS_STILL','FOCUS_SAF')
    
    attempts = 0
    while attempts < 10:
        try:
	    GPIO.output(LEDpins[i],GPIO.HIGH)
            cam.takePicture()
	    GPIO.output(LEDpins[i],GPIO.LOW)
            
            break
        except requests.exceptions.HTTPError as err:
            # leave the script ?
            # Recreate camera object?
	    GPIO.output(LEDpins[i],GPIO.LOW)
            pass
        except OlympusAirError as err:
	    GPIO.output(LEDpins[i],GPIO.LOW)
            if err.value == OlympusAirError.AF:
                print 'Autofocus error'
                cam.setProperty('FOCUS_STILL','FOCUS_MF')
        
        attempts = attempts + 1


cam.waitOnCardWrite()	


cam.stopPreview()

for i in range(len(LEDpins)):
	jpeg, raw = cam.getLatestFile(i)
    
        jpegFile = open(dirPath + '/' + 'LED%02i.jpg' % (len(LEDpins) - i),'w')
        jpegFile.write(jpeg)
    
        rawFile = open(dirPath + '/' + 'LED%02i.orf' % (len(LEDpins) - i),'w')
        rawFile.write(jpeg)
  
# What if we tried enough times
 

# Remove captured files
try:
	cam.switchMode('standalone')
	cam.switchMode('play')
	cam.switchMode('playmaintenance')  

	cam.removeAllFiles()
except:
	pass


cam.disconnect()



