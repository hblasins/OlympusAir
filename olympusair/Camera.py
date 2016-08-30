# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>


import requests
import socket
import xmltodict
import datetime

from collections import OrderedDict
from datetime import date
from struct import *


import olympusair

class Camera:
    
    IP = '192.168.0.10'
    headers = {'User-Agent':'OlympusCameraKit'}
    eventTimeout = 2
    
    
    def __init__(self, evPort=65000, lvPort=65001):
        
	self.eventSocket = None
	self.lvSocket = None
	self.eventPort = None
	self.lvPort = None

	print 'Camera init:',
	headers = {'User-Agent':'OlympusCameraKit'}
        req = requests.get('http://' + Camera.IP + '/get_connectmode.cgi',headers=headers)
    	req.raise_for_status()

        if (xmltodict.parse(req.text)['connectmode'] == 'OPC'):
            print 'OK'
        else:
            print 'Failed'
	    return
        

        print 'Establishing camera event notification:',
        params={'port':evPort}
        req = requests.get('http://' + Camera.IP + '/start_pushevent.cgi',headers=headers,params=params)
	req.raise_for_status()
	print 'OK'	
        
        
       
        # Establish an event socket. Keep trying untill you succeed
        print 'Establishing event socket, port %i: ' % evPort,
        
      
        self.eventSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.eventSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.eventSocket.settimeout(2)
        self.eventSocket.connect((Camera.IP,evPort))
    
	print 'OK'
        
        self.eventPort = evPort   
        self.lvPort = lvPort
        
        
    def __str__(self):
        state = self.getState()
 
        
        res = 'OlympusAir camera: \n'
        res = res + '>> WiFi: %s\n' % self.getProperty('SSID',verbose=False)
        res = res + '>> Battery level: %s\n' % self.getProperty('BATTERY_LEVEL',verbose=False)

        res = res + '>> Memory Card: \n'
        res = res + '   Status: %s\n' % state['cardstatus']
        res = res + '   Capacity: %i MB\n' % (float(state['cardremainbyte'])/1000000)
        res = res + '>> Lens:\n'
        res = res + '   Status: %s\n' % state['lensmountstatus']
        res = res + '   Focal length: %s mm\n' % state['focallength']
        res = res + '   Focal length range: %s to %s mm\n' % (state['widefocallength'],state['telefocallength'])
        res = res + '   Motorized zoom: %s\n' % state['electriczoom']
        
        return res

        
    def disconnect(self,verbose=True):
        if verbose:
            print 'Disconnecting camera:',
        req = requests.get('http://192.168.0.10/stop_pushevent.cgi',headers=self.headers)

        if verbose:
            if req.status_code == 200:
                print 'OK'
            else:
                print 'Failed'
        
        self.eventSocket.close()

            
            
    def commInterface(self,interface='wifi'):        
        print 'Camera communication mode change to %s:' % interface,
        params = {'path':interface}
        
        req = requests.get('http://192.168.0.10/switch_commpath.cgi',headers = self.headers, params = params)
        if req.status_code == 200:
            print 'OK'
        else:
            print 'Failed'
        
        
        
        
        
    def getState(self):
        req = requests.get('http://192.168.0.10/get_state.cgi',headers=self.headers)

        if req.status_code == 200:
            return xmltodict.parse(req.text)['response']
        else:
            return []

        
        
        
        
    def switchMode(self,mode):
        print 'Camera mode change to %s:' % mode,
        params = {'mode':mode}
        req = requests.get('http://' + Camera.IP + '/switch_cameramode.cgi',headers=self.headers,params=params)
	req.raise_for_status()        

        if xmltodict.parse(req.text)['result'] == 'OK':
            print 'OK'
        else:
            print 'Failed'
	    return
        
        
        selected, event = self.waitForEvent([olympusair.Event.MODE_CHANGE])
        
    def getFolderList(self,dirName='/DCIM'):
        params = {'DIR':dirName}
        req = requests.get('http://' + Camera.IP + '/get_imglist.cgi',headers=self.headers,params=params)
	req.raise_for_status()

	folderList = []
	for l in req.text.splitlines()[1:]:
            folderList.append(l.split(',')[1])

        return folderList
    
    
    def getFilesList(self,dirName='/DCIM'):

        folderList = self.getFolderList(dirName)

        rawFilesList = []
	jpegFilesList = []
        for folder in folderList:
        
            params = {'DIR':dirName + '/' + folder}
            req = requests.get('http://' + Camera.IP + '/get_imglist.cgi',headers=self.headers,params=params)
            req.raise_for_status()        
        
        
            for l in req.text.splitlines()[1:]:
		currFile = olympusair.File(l.split(','))
	   	if currFile.fileName.split('.')[1] == 'JPG':
			jpegFilesList.append(currFile)
		if currFile.fileName.split('.')[1] == 'ORF':
			rawFilesList.append(currFile)
        
        return jpegFilesList, rawFilesList
    
    
    
    
    
        

    def getFile(self,path):
        req = requests.get('http://' + Camera.IP + path,headers=self.headers)
        
        
        return req
    
    
    def getLatestFile(self,id=0):
        
        jpegList, rawList = self.getFilesList()
        

	jpegList.sort(reverse = True)
        rawList.sort(reverse = True)

	# print jpegList

	if id < len(jpegList):

		name = jpegList[id].fileName.split('.')[0]

		# print 'Retreiving file %s', name
		jpegFile = self.getFile(jpegList[id].directory + '/' + jpegList[id].fileName)

		for j in rawList:
			rawName, format = j.fileName.split('.')
			if rawName == name and format=='ORF':
				rawFile = self.getFile(j.directory + '/' + j.fileName)
				return jpegFile.content, rawFile.content

		return jpegFile.content, None

	return None, None

    def getLatestFileNames(self,id=0):
        
        jpegList, rawList = self.getFilesList()
        

	jpegList.sort(reverse = True)
        rawList.sort(reverse = True)

	# print jpegList

	if id < len(jpegList):

		jpegName = jpegList[id].fileName.split('.')[0]

		for j in rawList:
			rawName, frmt = j.fileName.split('.')
			if rawName == jpegName and frmt=='ORF':
                                jpegName = jpegList[id].directory + '/' + jpegName
                                rawName = rawList[id].directory + '/' + rawName
				return jpegName, rawName

                jpegName = jpegList[id].directory + '/' + jpegName
		return jpegName, None

	return None, None
        
    
    def removeFileProtection(self):
	print 'Removing file protection',
	req = requests.get('http://' + Camera.IP + '/release_allprotect.cgi',headers = self.headers)
	req.raise_for_status()

	if xmltodict.parse(req.text)['result'] == 'OK':
		print 'OK'
	else:
		print 'Failed'

    def removeFile(self,path):
	params = {'DIR':path}
	print 'Erasing file %s:' % path,
	req = requests.get('http://' + Camera.IP + '/exec_erase.cgi',headers = self.headers,params=params)
	req.raise_for_status()

	if xmltodict.parse(req.text)['result'] == 'OK':
		print 'OK'
	else:
		print 'Failed'

    def removeAllFiles(self):
	jpegList, _ = self.getFilesList()

        # If there are JPG + RAW files then removing JPG will also remove RAW
	for f in jpegList:
		self.removeFile(f.directory + '/' + f.fileName)

        _, rawList = self.getFilesList()
	for f in rawList:
		self.removeFile(f.directory + '/' + f.fileName)



    
    def getResizedFile(self, path, size):
        headers = {'User-Agent':'OlympusCameraKit'}
        params = {'DIR':path,'size':size}
        
        
        req = requests.get('http://' + Camera.IP + '/get_resizeimg.cgi',headers=headers,params=params)
        print req.status_code
        
        return req
    
    
    
    
    
    
    def setZoom(self, focalLength):
        
        print 'Camera zoom set to %i:' % focalLength,
        params = OrderedDict([('com','newctrlzoom'),('ctrl','start'),('dir','fix'),('focallen',focalLength)])
        
        req = requests.get('http://192.168.0.10/exec_takemisc.cgi',headers=self.headers,params=params)
        
        if req.status_code == 200 and (xmltodict.parse(req.text)['result'] == 'OK'):
            print 'OK' 
        else:
            print 'Failed'
            return
            
        selected, event = self.waitForEvent([122])

   
            
            
            
            
    def getEventNotifications(self,sock):
        
        i = 0
        
        buff = sock.recv(1024)
	# print buff
        eventList = []
        while i < len(buff)-1:
            appID = ord(buff[i+0])
            event = ord(buff[i+1])
            length = ord(buff[i+2])*256 + ord(buff[i+3])
            data = buff[(i+4):(i+4+length)]
                
            event = olympusair.Event(appID,event,data)
            # print event
            i = i+4+length
            eventList.append(event)
        
        return eventList
    
    def findEvent(self,eventList,eventID):
        sel = [None] * len(eventID)
        found = [False] * len(eventID)
         
        for e in eventList:
             # print e 
             if e.eventID in eventID:
                 found[eventID.index(e.eventID)] = True
                 sel[eventID.index(e.eventID)] = e
            
        return found, sel
    
    def waitForEvent(self,eventID,mode = 'AND'):

        found = [False]*len(eventID)
        event = [None]*len(eventID)
        # print found
        
        
        att=0
        while att < Camera.eventTimeout:
 
            try:
                eventList = self.getEventNotifications(self.eventSocket)
                tmpFound, tmpEvent = self.findEvent(eventList,eventID)
                # print att, found, tmpFound, tmpEvent
                event = [i if j else k for (i,j,k) in zip(tmpEvent,tmpFound,event)]
                found = [i or j for (i,j) in zip(tmpFound,found)]                                          
                
                # print found
                if mode == 'AND':
                    if all(found):
                        return found, event
                else:
                    if any(found):
                        return found, event
                
            except socket.timeout as err:
		att = att+1
                print 'Waiting for events, attempt %i/%i' % (att,Camera.eventTimeout)
            
        print 'Timeout reached'    
        # print found, event
        return found, event
            
        
    def getProperty(self,propName,verbose=True):

        if verbose:
            print 'Camera property %s read' % propName,
        params=OrderedDict([('com','desc'),('propname',propName)])
        req = requests.get('http://' + Camera.IP + '/get_camprop.cgi',headers=self.headers,params=params)
        req.raise_for_status()

        
        state = xmltodict.parse(req.text)['desc']['value']
        allowedStates = xmltodict.parse(req.text)['desc']['enum']
        if verbose:
            print '%s (%s): OK' % (state,allowedStates)
        return state
        
        
 
    def setProperty(self, propName, propVal):
        
        # We need to get the property first. Setting a property to a value that is equal to the old value does not always
        # work.
        currentVal = self.getProperty(propName)
        print 'Camera property %s change to %s:' % (propName,propVal), 
        if currentVal != propVal:
            params = OrderedDict([('com','set'),('propname',propName)])
            payload = '<?xml version="1.0"?><set><value>%s</value></set>\n' % (propVal)
        
            req = requests.post('http://' + Camera.IP + '/set_camprop.cgi',headers=self.headers,params=params,data=payload)
	    req.raise_for_status()    
	    print 'OK'
            
            selected, event = self.waitForEvent([olympusair.Event.PROPERTY_CHANGE])
	    if selected == False:
		raise olympusair.Error(olympusair.Error.PROPERTY_NOT_CHANGED)

            # for (i,j) in zip(selected,event):
            #    print i,j
        else:
            print  'Not needed'
        
        
        
        
        
        
    def startPreview(self,resolution = '0320x0240'):
        
        
        print 'Establishing liveview socket %i:' % self.lvPort,    
        self.lvSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) #UDP
	self.lvSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.lvSocket.bind(('',self.lvPort))
        self.lvSocket.settimeout(5)
        print 'OK' 
            
        
        
        
        print 'Camera live view resolution change to %s:' % resolution,
        params = OrderedDict([('com','changelvqty'),('lvqty',resolution)])
        req = requests.get('http://' + Camera.IP + '/exec_takemisc.cgi',headers=self.headers,params=params)
	req.raise_for_status()

	if (xmltodict.parse(req.text)['result'] == 'OK'):
            print 'OK'
        else:
            raise olympusair.Error(olympusair.Error.PREVIEW_RES_CHANGE)
        
        
        
        print 'Camera live view start:',
        params = OrderedDict([('com','startliveview'),('port',self.lvPort)])
        req = requests.get('http://' + Camera.IP + '/exec_takemisc.cgi',headers=self.headers,params=params)
	req.raise_for_status()        
        print 'OK'
        
        
        
        data = self.lvSocket.recvfrom(128)

        if len(data) == 0:
            raise olympusair.Error(olympusair.Error.PREVIEW_DATA_UNAVAILABLE)
        
            
        
    def takePicture(self):
        print 'Camera picture acquisition:',
        params = OrderedDict([('com','newstarttake')])
        req = requests.get('http://' + Camera.IP + '/exec_takemotion.cgi',headers=self.headers,params=params)
        req.raise_for_status()
      	print 'OK'
	
        
        eventIDs = [olympusair.Event.AUTO_FOCUS_RESULT,
		    olympusair.Event.READY_TO_CAPTURE,
		    olympusair.Event.CAPTURE_STARTED,
		    olympusair.Event.CAPTURE_FINISHED,
		    olympusair.Event.CAPTURE_PROCESS_FINISHED]
        ind, event = self.waitForEvent(eventIDs)

	# Raise an error if the camera could not focus
	if ind[0] == True and xmltodict.parse(event[0].data)['root']['result'] == 'ng':
		raise olympusair.Error(olympusair.Error.AF)
	
	# Raise an error if a capture was not finished
	if ind[3] == False:
		raise olympusair.Error(olympusair.Error.CAPTURE_FAILED)


	# for (i,j,k) in zip(eventIDs,ind,event):
        # 	print i,j,k
        
        
    def stopPreview(self):
        print 'Camera live view stop:',
        params = OrderedDict([('com','stopliveview')])
        req = requests.get('http://' + Camera.IP + '/exec_takemisc.cgi',headers=self.headers,params=params)
        req.raise_for_status()
	print 'OK'
        
        if self.lvSocket != None:
        	self.lvSocket.close()
        

    def waitOnCardWrite(self):
	

	frame = olympusair.LiveViewFrame()
	frame.getLiveViewFrame(self.lvSocket)

	nFrames = 0
	while frame.cardWriteInProgress == 0 and nFrames < 1000:
		frame.getLiveViewFrame(self.lvSocket)
		nFrames = nFrames + 1
		# print 'Write not started, getting frame %i/%i' % (nFrames,1000)

	nFrames = 0
	while frame.cardWriteInProgress == 1 and nFrames < 1000:
		frame.getLiveViewFrame(self.lvSocket) 
		nFrames = nFrames + 1
		# print 'Write started, getting frame %i/%i' % (nFrames,1000)

	
