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

dirPath = './' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
print '======= ' + dirPath + ' ======='
os.mkdir(dirPath)

cam = OlympusAir()
cam.commInterface()
cam.switchMode('standalone')
cam.switchMode('rec')
cam.getProperty('BATTERY_LEVEL')
cam.setProperty('FOCUS_STILL','FOCUS_SAF')
cam.setProperty('RAW','ON')
cam.setProperty('TAKE_DRIVE','DRIVE_NORMAL')
cam.setProperty('TAKEMODE','A')
cam.setProperty('DESTINATION_FILE','DESTINATION_FILE_MEDIA')
cam.setProperty('EXPREV','-1.0')
cam.setProperty('AE','AE_ESP')
cam.setProperty('APERTURE','2.8')
cam.setProperty('ISO','1600')

 


cam.startPreview()

for i in range(len(LEDpins)+1):
    
    # cam.setProperty('FOCUS_STILL','FOCUS_SAF')
    
    attempts = 0
    while attempts < 10:
        try:
	    if i < len(LEDpins):
	    	GPIO.output(LEDpins[i],GPIO.HIGH)
            	cam.takePicture()
	    	GPIO.output(LEDpins[i],GPIO.LOW)
	    else:
		cam.takePicture()
            
            break
        except requests.exceptions.HTTPError as err:
            # leave the script ?
            # Recreate camera object?
	    if i < len(LEDpins):
	    	GPIO.output(LEDpins[i],GPIO.LOW)
            
        except OlympusAirError as err:
	    if i < len(LEDpins):
	    	GPIO.output(LEDpins[i],GPIO.LOW)
            if err.value == OlympusAirError.AF:
                print 'Autofocus error'
                cam.setProperty('FOCUS_STILL','FOCUS_MF')
        
        attempts = attempts + 1


cam.waitOnCardWrite()	
cam.stopPreview()

for i in range(len(LEDpins) + 1):
	jpeg, raw = cam.getLatestFile(i)

	if i < 1:
		fName = 'Ambient'
		
	else:
		fName = 'LED%02i' % (len(LEDpins) - i + 1)

        jpegFile = open(dirPath + '/' + fName + '.jpg' ,'w')
        jpegFile.write(jpeg)
    
        rawFile = open(dirPath + '/' + fName + '.orf','w')
        rawFile.write(jpeg)
  
# What if we tried enough times
 

# Remove captured files
try:
	cam.switchMode('standalone')
	cam.switchMode('play')
	cam.switchMode('playmaintenance')  

	cam.removeAllFiles()
except:
	cam.disconnect()
	GPIO.cleanup();

GPIO.cleanup()
cam.disconnect()



