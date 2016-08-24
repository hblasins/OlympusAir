
# coding: utf-8

# In[ ]:

import olympusair
import os
import datetime
import cv2
import sys


# In[ ]:

cam = olympusair.Camera()
cam.commInterface()

print cam


cam.switchMode('standalone')
cam.switchMode('rec')
cam.setProperty('RAW','ON')
cam.setProperty('TAKE_DRIVE','DRIVE_NORMAL')
cam.setProperty('TAKEMODE','P')
cam.setProperty('DESTINATION_FILE','DESTINATION_FILE_MEDIA')

cam.switchMode('standalone')
cam.switchMode('play')
cam.switchMode('playmaintenance')
print cam.getFilesList()
cam.removeFileProtection()
cam.removeAllFiles()
print cam.getFilesList()


# In[ ]:

cam.switchMode('standalone')
cam.switchMode('rec')

destPath = os.path.join('/','media','pi','REEF')
if not os.path.exists(destPath):
    os.makedirs(destPath)

elapsed = datetime.datetime.now()

while(1):
    startTime = elapsed
            
    print '>> %s: Acquiring a photo' % elapsed.strftime('%Y-%m-%d_%H-%M-%S')
        
    print cam
        
    cam.startPreview()
    cam.takePicture()
    cam.waitOnCardWrite()
    cam.stopPreview()
            
    jpeg, raw = cam.getLatestFile()
                        
    dirPath =  os.path.join(destPath,elapsed.strftime('%Y-%m-%d_%H-%M-%S'))
    if not os.path.exists(dirPath):
        os.mkdir(dirPath)
    
    if jpeg != None:
        jpegFile = open(os.path.join(dirPath,'IMG.jpg'),'w')
        jpegFile.write(jpeg)
        jpegFile.close()
    
    if raw != None:
        rawFile = open(os.path.join(dirPath,'IMG.orf'),'w')
        rawFile.write(raw)
        rawFile.close()
    
    # Remove all files
    cam.switchMode('standalone')
    cam.switchMode('play')
    cam.switchMode('playmaintenance')
    cam.removeAllFiles()
    cam.switchMode('standalone')
    cam.switchMode('rec')
    
    elapsedTimer = datetime.datetime.now()
    while (elapsed - startTime) < datetime.timedelta(minutes=5):
        elapsed = datetime.datetime.now()
        if (elapsed - elapsedTimer) > datetime.timedelta(seconds=1):
            td = datetime.timedelta(minutes=5) - (elapsed - startTime)
            sys.stdout.write('Next capture in %i seconds \r' % td.seconds)
            sys.stdout.flush()
            elapsedTimer = datetime.datetime.now() 
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    
        


# In[ ]:

cam.disconnect()


# In[ ]:



