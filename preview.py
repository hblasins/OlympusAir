
# coding: utf-8

# In[1]:

import cv2
import olympusair
import numpy as np


# In[2]:

cam = olympusair.Camera()


# In[3]:

cam.commInterface()


# In[4]:

print cam.getState()


# In[5]:

cam.switchMode('standalone')


# In[6]:

cam.switchMode('rec')


# In[7]:

cam.getProperty('FOCUS_STILL')
cam.setProperty('FOCUS_STILL','FOCUS_MF')
cam.getProperty('FOCUS_STILL')

cam.getProperty('RAW')
cam.setProperty('RAW','ON')
cam.getProperty('RAW')

cam.getProperty('TAKE_DRIVE')
cam.setProperty('TAKE_DRIVE','DRIVE_NORMAL')
cam.getProperty('TAKE_DRIVE')

cam.getProperty('TAKEMODE')
cam.setProperty('TAKEMODE','P')
cam.getProperty('TAKEMODE')

cam.getProperty('DESTINATION_FILE')
cam.setProperty('DESTINATION_FILE','DESTINATION_FILE_MEDIA')
cam.getProperty('DESTINATION_FILE')


# In[8]:

cam.startPreview()


# In[10]:


while (1):
    lvFrame = olympusair.LiveViewFrame()
    lvFrame.getLiveViewFrame(cam.lvSocket)
    tst = np.fromstring(lvFrame.jpegStream, dtype = np.uint8)


    img = cv2.imdecode(tst,1)

    cv2.imshow('Preview',img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
        
cv2.destroyAllWindows()


# In[ ]:

cam.stopPreview()
cam.disconnect()



# In[ ]:



