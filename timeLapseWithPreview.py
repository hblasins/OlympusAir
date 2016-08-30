
# coding: utf-8

# In[ ]:

import olympusair
import os
import datetime
import cv2
import sys
import numpy as np
import time

nLEDs = 7
evSet = [-3.0, 0.0]

def main(argv):

    cam = olympusair.Camera()
    cam.commInterface()

    print cam

    cam.switchMode('standalone')
    cam.switchMode('rec')
    cam.setProperty('TAKEMODE','P')
    cam.setProperty('RAW','ON')
    cam.setProperty('ISO','Auto')
    cam.setProperty('FOCUS_STILL','FOCUS_SAF')
    cam.setProperty('AE_LOCK_STATE','UNLOCK')
    cam.setProperty('TAKE_DRIVE','DRIVE_NORMAL')
    cam.setProperty('AE','AE_ESP')
    cam.setProperty('DESTINATION_FILE','DESTINATION_FILE_MEDIA')

    cam.setProperty('EXPREV','0.0')

    destPath = os.path.join('/','media','pi','REEF')
    if not os.path.exists(destPath):
        os.makedirs(destPath)

    elapsed = datetime.datetime.now()


    cv2.namedWindow('Preview',cv2.WINDOW_AUTOSIZE)
    # cv2.setWindowProperty('Preview',cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    # cv2.resizeWindow('Preview',640,480)
    cv2.moveWindow('Preview',10,30)

    captureCounter = 0;

    while(1):

        cam.startPreview('0640x0480')

        startTime = elapsed

        while (elapsed - startTime) < datetime.timedelta(minutes=float(argv[0])):
            elapsed = datetime.datetime.now()

            td = datetime.timedelta(minutes=float(argv[0])) - (elapsed - startTime)

            lvFrame = olympusair.LiveViewFrame()
            lvFrame.getLiveViewFrame(cam.lvSocket)
            tst = np.fromstring(lvFrame.jpegStream, dtype = np.uint8)


            img = cv2.imdecode(tst,1)
            cv2.putText(img,'S: %i/%is A: f#%.1f' % (lvFrame.shutterCurrNum,lvFrame.shutterCurrDenom,lvFrame.fNumberCurr), 
               (10,15),cv2.FONT_HERSHEY_PLAIN,1,(0,0,255))
            cv2.putText(img,'ISO: %i' % (lvFrame.iso),(10,30),cv2.FONT_HERSHEY_PLAIN,1,(0,255,0))
            cv2.putText(img,'Timer: %i sec' % td.seconds,(10,45),cv2.FONT_HERSHEY_PLAIN,1,(255,0,255))
            cv2.putText(image,'Caputres %i' % captureCounter, cv2.FONT_HERSHEY_PLAIN,1,(255,0,255))

            if img is not None:
                cv2.imshow('Preview',img)
            else:
                print '>> Zero image !!'
        
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cam.stopPreview()
                cam.disconnect()
                sys.exit(0)

            
        print '>> %s: Acquiring a set of photos' % elapsed.strftime('%Y-%m-%d_%H-%M-%S')
        print cam

        captureCounter += 1

        for ev in evSet:

            cam.setProperty('EXPREV','%.1f' % ev)
            
            for i in range(nLEDs+1):

                # Turn led on
                cam.takePicture()
                # Turn led off

            cam.waitOnCardWrite()
        
        cam.stopPreview()

        for ev in evSet:

            evIndex = evSet.index(ev)

            dirPath =  os.path.join(destPath,elapsed.strftime('%Y-%m-%d_%H-%M-%S'),'%02i_EV_%.1f' % (evIndex,ev))
            if not os.path.exists(dirPath):
                os.makedirs(dirPath)

            logFile = open(os.path.join(dirPath,'log.txt'),'w')

            
            for i in range(nLEDs+1):

                fileIndex = (nLEDs+1)*(len(evSet) - evIndex) - 1 - i
        
                jpeg, raw = cam.getLatestFileNames(fileIndex)

                if i == 0:
                    fName = 'Ambient'
                else:
                    fName = 'LED_%i' % i       

                logFile.write('%s; %s\n' % (fName,jpeg))
            logFile.close()             
                # if jpeg != None:                
                    # jpegFile = open(os.path.join(dirPath,fName + '.jpg'),'w')
                    # jpegFile.write(jpeg)
                    # jpegFile.close()
    
                # if raw != None:
                    # rawFile = open(os.path.join(dirPath,fName + '.orf'),'w')
                    # rawFile.write(raw)
                    # rawFile.close()

    
    cam.stopPreview()
    cam.disconnect()


if __name__ == "__main__":
    main(sys.argv[1:])


