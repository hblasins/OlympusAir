# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>


import requests
import socket
import xmltodict
import datetime

from collections import OrderedDict
from datetime import date
from struct import *
from PIL import Image

class OlympusAirLiveViewFrame:

	ISO_LOW = 0xFFFE
	AF_NA = 0
	AF_OK = 1
	AF_FAILED = 2

	def __str__(self):
		res = 'Live View Frame ID: %i\n' % self.frameID
		res = res +  'Live View Jpeg file size: %i bytes\n' % self.jpegSize
		res = res +  'AF  %i, (%i,%i) width: %i, height: %i\n' % (self.afType, self.afXcoord, self.afYcoord, self.afWidth, self.afHeight)
		res = res +  'Card status, full: %i, protected: %i, error: %i, write: %i, mounted: %i\n' % (self.cardNotFull, self.cardProtected, self.cardError, self.cardWriteInProgress, self.cardMounted)
		res = res +  'Orientation: %i degrees\n' % self.orientation
		res = res +  'Storage capacity: %i frames\n' % self.capacity
		res = res +  'Shutter: %i/%i, max: %i/%i, min: %i/%i\n' % (self.shutterCurrNum, self.shutterCurrDenom, self.shutterMaxNum, self.shutterMaxDenom, self.shutterMinNum, self.shutterMinDenom )
		res = res +  'fNumber: %f , max: %f, min %f\n' % (self.fNumberCurr, self.fNumberMax,  self.fNumberMin)
		res = res +  'ISO %i, auto: %i, warning: %i\n' % (self.iso, self.isoAuto, self.isoWarning)
		res = res +  'Focus mode: %i\n' % self.focusMode
		res = res +  'Zoom: %i mm, min: %i mm, max %i mm\n' % (self.zoomCurr,self.zoomWide,self.zoomTele)
		return res

	def showImage(self):
		img = Image.open(StringIO(self.jpegStream))
		img.show()

	def getLiveViewFrame(self,port):

		firstFrameRecvd = False	
		frameComplete = False	

		nIter = 0
		while frameComplete == False and nIter < 100:
			data = port.recvfrom(4096)

			V, P, X, CC, M, PT, RTPseq, FrameSeq = self.decodeHeader(data[0])				
			# print V, P, X, CC, M, PT, RTPseq, FrameSeq

			# If first frame:
			if V==2 and P==0 and X==1 and M==0 and PT==96 and firstFrameRecvd==False:
				# print 'Got first packet!'
				packetID = RTPseq
				self.frameID = FrameSeq
				firstFrameRecvd = True
			
				# If this is the first frame, decode the extension header
				self.decodeExtensionHeader(data[0][12:])

				# Get the reminder of data 
				self.jpegStream = data[0][12 + self.length*4 + 4:]
				# print len(self.jpegStream)
				# print self.jpegStream[0:2].encode('hex')

			# If subsequent frame:
			elif V==2 and P==0 and X==0 and CC==0 and M == 0 and PT==96 and firstFrameRecvd==True and (packetID+1) == RTPseq and self.frameID == FrameSeq:
				
				# print 'Got subsequent packet(s)!'
				self.jpegStream = self.jpegStream + data[0][12:]
				packetID = packetID + 1

			# If last frame:
			elif V==2 and P==0 and X==0 and CC==0 and M == 1 and PT==96 and firstFrameRecvd==True and (packetID+1) == RTPseq and self.frameID == FrameSeq:	
				# print 'Got last packet!'
				self.jpegStream = self.jpegStream + data[0][12:]
				# print 'Length %i, actual %i' % (self.jpegSize, len(self.jpegStream))
				# print 'Last ' + self.jpegStream[len(self.jpegStream)-2:].encode('hex')
				frameComplete = True
			else:
				# print 'Resetting'
				firstFrameRecvd = False
				frameComplete = False


			nIter = nIter + 1


	def decodeHeader(self,data):

		if len(data) > 12:
				
			V = (ord(data[0]) & 0xD0) >> 6
			P = (ord(data[0]) & 0x20) >> 5
			X = (ord(data[0]) & 0x10) >> 4
			CC = (ord(data[0]) & 0xF)

			M = (ord(data[1]) & 0x80) >> 7
			PT = ord(data[1]) & 0x7F 
			
			RTPseq = unpack_from('!H',data[2:4])[0]
			FrameSeq = unpack_from('!I',data[4:8])[0]

			return V, P, X, CC, M, PT, RTPseq, FrameSeq
		return None, None, None, None, None, None, None, None


	def decodeExtensionHeader(self,data):
		
		self.version = unpack_from('!H',data[0:2])[0]
		self.length = unpack_from('!H',data[2:4])[0]
		# print self.version, self.length


		currentPos = 4
		while currentPos < (4*self.length + 4):
		
			funcID = unpack_from('!H',data[currentPos:currentPos+2])[0]
			length = unpack_from('!H',data[currentPos+2:currentPos+4])[0]

			# print funcID, length
			subdata = data[currentPos+4:currentPos+4 + 4*length]
			if funcID == 1:
				self.decodeJPEGSize(subdata)
			elif funcID == 2:
				self.decodeAFInfo(subdata)
			elif funcID == 3:
				self.decodeCardStatus(subdata)
			elif funcID == 4:
				self.decodeOrientation(subdata)
			elif funcID == 5:
			 	self.decodeStorageCapacity(subdata)
			elif funcID == 8:
			 	self.decodeShutterSpeed(subdata)
			elif funcID == 9:
				self.decodefNumber(subdata)
			elif funcID == 10:
				self.decodeEV(subdata)
			elif funcID == 12:
				self.decodeISO(subdata)
			elif funcID == 16:
				pass
			elif funcID == 17:
				self.decodeFocusMode(subdata)
			elif funcID == 18:
				self.decodeZoom(subdata)

			currentPos = currentPos + length*4 + 4

		return True

	def decodeJPEGSize(self,data):
		self.jpegSize = unpack_from('!I',data)[0]

		# print 'Jpeg size %i' % self.jpegSize

	def decodeAFInfo(self,data):
		self.afType = unpack_from('!I',data[0:4])[0]
		self.afXcoord = unpack_from('!I',data[4:8])[0]
		self.afYcoord = unpack_from('!I',data[8:12])[0]
		self.afWidth = unpack_from('!I',data[12:16])[0]
		self.afHeight = unpack_from('!I',data[16:24])[0]

		# print 'AF %i %i %i %i %i' % (self.afType,self.afXcoord, self.afYcoord, self.afWidth, self.afHeight)

	def decodeCardStatus(self,data):

		tmp = unpack_from('!I',data)[0]

		self.cardMounted = ((tmp & 0x3) >> 1) == 1
		self.cardNotFull = ((tmp & 0x4) >> 2) == 1
		self.cardProtected = ((tmp & 0x8) >> 3) == 1
		self.cardError = ((tmp & 0x10) >> 4) == 1
		self.cardWriteInProgress = ((tmp & 0x20) >> 5) == 1
		

		# print 'Card status %i %i %i %i %i' % (self.cardNotFull, self.cardProtected, self.cardError, self.cardWriteInProgress, self.cardMounted)

	def decodeOrientation(self,data):
		orient = unpack_from('!I',data)[0]
		if orient == 1:
			self.orientation = 0
		elif orient == 3:
			self.orientation = 180
		elif orient == 6:
			self.orientation = 90
		elif orient == 8:
			self.orientaion = 270
		else:
			self.orientation = -1

		# print 'Orientation %i' % self.orientation

	def decodeStorageCapacity(self,data):
		self.capacity = unpack_from('!I',data)[0]

		# print 'Storage capacity %i' % self.capacity

	def decodeShutterSpeed(self,data):


		self.shutterMinNum = unpack_from('!H',data[0:2])[0]
		self.shutterMinDenom = unpack_from('!H',data[2:4])[0]
		self.shutterMaxNum = unpack_from('!H',data[4:6])[0]
		self.shutterMaxDenom = unpack_from('!H',data[6:8])[0]
		self.shutterCurrNum = unpack_from('!H',data[8:10])[0]
		self.shutterCurrDenom = unpack_from('!H',data[10:12])[0]

		# print 'Shutter %i/%i to %i/%i curr %i/%i' % (self.shutterMinNum, self.shutterMinDenom, self.shutterMaxNum, self.shutterMaxDenom, self.shutterCurrNum, self.shutterCurrDenom)
	
	def decodefNumber(self,data):
		self.fNumberMin = float(unpack_from('!I',data[0:4])[0])/10
		self.fNumberMax = float(unpack_from('!I',data[4:8])[0])/10
		self.fNumberCurr = float(unpack_from('!I',data[8:12])[0])/10

		# print 'fNumber %f to %f, curr %f' % (self.fNumberMin, self.fNumberMax, self.fNumberCurr)

	def decodeEV(self,data):
		self.evMin = float(unpack_from('!i',data[0:4])[0])/10
		self.evMax = float(unpack_from('!i',data[4:8])[0])/10
		self.evCurr = float(unpack_from('!i',data[8:12])[0])/10

		# print 'EV %f to %f, curr %f' % (self.evMin, self.evMax, self.evCurr)	

	def decodeISO(self,data):
		
		self.iso = unpack_from('!I',data[0:4])[0]
		self.isoAuto = unpack_from('H',data[4:6])[0] == 1
		self.isoWarning = unpack_from('I',data[8:12])[0] == 1

		# print 'ISO %i, auto %i, warning %i' % (self.iso, self.isoAuto, self.isoWarning)

	def decodeFocusMode(self,data):
		self.focusMode = unpack_from('!H',data[0:2])[0]

		# print 'Focus mode %i' % self.focusMode

	def decodeZoom(self,data):
		self.zoomWide = unpack_from('!H',data[2:4])[0]
		self.zoomCurr = unpack_from('!H',data[4:6])[0]
		self.zoomTele = unpack_from('!H',data[6:8])[0]

		# print 'Zoom %i to %i, curr %i' % (self.zoomWide,self.zoomTele,self.zoomCurr)

	

class OlympusAirEvent:

    BATTERY_LEVEL = 2
    AUTO_FOCUS_RESULT = 101
    READY_TO_CAPTURE = 102
    CAPTURE_STARTED = 103
    CAPTURE_FINISHED = 106
    CAPTURE_PROCESS_FINISHED = 107
    PREVIEW_IMAGE_GENERATED = 108
    MOVIE_STOPPED = 110
    MOVIE_START = 135
    PROGRESS_CHANGED = 111
    IMAGE_TRANSFER_REQ = 117
    LENS_MOUNT_STATUS_CHANGE = 120
    LENS_DRIVE_STOPPED = 122
    CARD_MOUNT_CHANGE = 132
    TEMPERATURE_CHANGE = 133
    MEDIA_PROTECTION_REMOVED = 134
    MODE_CHANGE = 201
    PROPERTY_CHANGE = 206


    def __init__(self,appID,eventID,data):
        self.appID = appID
        self.eventID = eventID
        self.data = data
    
    def __str__(self):
        return 'appID: %i; eventID: %i; data: %s' % (self.appID, self.eventID, self.data)
    
class OlympusAirFile:
    def __init__(self,paramList):
        self.directory = paramList[0]
        self.fileName = paramList[1]
        self.size = int(paramList[2])
        self.attr = int(paramList[3])
        self.date = int(paramList[4])
        self.time = int(paramList[5])
        
    def __repr__(self):
        return '(%s, %s, %i, %i, %s)' % (self.directory,self.fileName, self.size, self.attr, self.getDate().strftime('%Y-%m-%d_%H-%M-%S'))

    def __cmp__(self,other):
        if self.date > other.date:
            return 1
        elif self.date < other.date:
            return -1
        else:
            if self.time > other.time:
                return 1
            elif self.time < other.time:
                return -1
            else:
                if self.fileName > other.fileName:
			return 1
		else:
			return -1

    
    def getDate(self):
        
        day = int(self.date & 0x1f)
        month = int((self.date & 0x1e0) >> 5)
        year = int((self.date & 0xfe00) >> 9) + 1980
        
        sec = int(self.time & 0x1f)*2
        minutes = int((self.time & 0x7e) >> 5)
        hours = int((self.time & 0xf088) >> 11)
        
        
        return datetime.datetime(year,month,day,hours,minutes,sec)
        


class OlympusAirError(Exception):

	AF = 0
	PROPERTY_NOT_CHANGED = 1
	CAPTURE_FAILED = 2
	PREVIEW_RES_CHANGE = 3
	PREVIEW_DATA_UNAVAILABLE = 4

	def __init__(self,value):
		self.value = value

	def __str__(self):
		return 'OlympusAir error'






class OlympusAir:
    
    IP = '192.168.0.10'
    headers = {'User-Agent':'OlympusCameraKit'}
    eventTimeout = 20
    
    
    def __init__(self, evPort=65000, lvPort=65001):
        
	self.eventSocket = None
	self.lvSocket = None
	self.eventPort = None
	self.lvPort = None

	print 'Camera init:',
	headers = {'User-Agent':'OlympusCameraKit'}
        req = requests.get('http://' + OlympusAir.IP + '/get_connectmode.cgi',headers=headers)
    	req.raise_for_status()

        if (xmltodict.parse(req.text)['connectmode'] == 'OPC'):
            print 'OK'
        else:
            print 'Failed'
	    return
        

        print 'Establishing camera event notification:',
        params={'port':evPort}
        req = requests.get('http://' + OlympusAir.IP + '/start_pushevent.cgi',headers=headers,params=params)
	req.raise_for_status()
	print 'OK'	
        
        
       
        # Establish an event socket. Keep trying untill you succeed
        print 'Establishing event socket, port %i: ' % evPort,
        
      
        self.eventSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.eventSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.eventSocket.settimeout(2)
        self.eventSocket.connect((OlympusAir.IP,evPort))
    
	print 'OK'
        
        self.eventPort = evPort   
        self.lvPort = lvPort
        
        
        

        
    def disconnect(self):        
        print 'Disconnecting camera:',
        req = requests.get('http://192.168.0.10/stop_pushevent.cgi',headers=self.headers)
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
        req = requests.get('http://192.168.0.10/switch_cameramode.cgi',headers=self.headers,params=params)
        
        if req.status_code == 200 and xmltodict.parse(req.text)['result'] == 'OK':
            print 'OK'
        else:
            print 'Failed %i' % req.status_code
        
        
        selected, event = self.waitForEvent([OlympusAirEvent.MODE_CHANGE])
        
    
    
    
    def getFilesList(self,dirName='/DCIM/100OLYMP'):
        params = {'DIR':dirName}
        req = requests.get('http://192.168.0.10/get_imglist.cgi',headers=self.headers,params=params)
        
        if req.status_code == 404:
            print 'Not found'
            return None
        
        rawFilesList = []
	jpegFilesList = []
        for l in req.text.splitlines()[1:]:
		currFile = OlympusAirFile(l.split(','))
	   	if currFile.fileName.split('.')[1] == 'JPG':
			jpegFilesList.append(currFile)
		if currFile.fileName.split('.')[1] == 'ORF':
			rawFilesList.append(currFile)

            # filesList.append(OlympusAirFile(l.split(',')))
        
        return jpegFilesList, rawFilesList
    
    
    
    
    
        

    def getFile(self,path):
        req = requests.get('http://192.168.0.10' + path,headers=self.headers)
        
        
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
        
    
    
    def getResizedFile(self, path, size):
        headers = {'User-Agent':'OlympusCameraKit'}
        params = {'DIR':path,'size':size}
        
        
        req = requests.get('http://192.168.0.10/get_resizeimg.cgi',headers=headers,params=params)
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
                
            event = OlympusAirEvent(appID,event,data)
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
        while att < OlympusAir.eventTimeout:
 
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
                print 'Waiting for events, attempt %i/%i' % (att,OlympusAir.eventTimeout)
            
        print 'Timeout reached'    
        # print found, event
        return found, event
            
        
    def getProperty(self,propName):
   
        print 'Camera property %s read' % propName,
        params=OrderedDict([('com','desc'),('propname',propName)])
        req = requests.get('http://' + OlympusAir.IP + '/get_camprop.cgi',headers=self.headers,params=params)
        req.raise_for_status()

        
        state = xmltodict.parse(req.text)['desc']['value']
        allowedStates = xmltodict.parse(req.text)['desc']['enum']
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
        
            req = requests.post('http://' + OlympusAir.IP + '/set_camprop.cgi',headers=self.headers,params=params,data=payload)
	    req.raise_for_status()    
	    print 'OK'
            
            selected, event = self.waitForEvent([OlympusAirEvent.PROPERTY_CHANGE])
	    if selected == False:
		raise OlympusAirError(OlympusAirError.PROPERTY_NOT_CHANGED)

            # for (i,j) in zip(selected,event):
            #    print i,j
        else:
            print  'Not needed'
        
        
        
        
        
        
    def startPreview(self,resolution = '0320x0240'):
        
        
        print 'Establishing liveview socket %i:' % self.lvPort,    
        self.lvSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) #UDP
        self.lvSocket.bind(('',self.lvPort))
        self.lvSocket.settimeout(5)
        print 'OK' 
            
        
        
        
        print 'Camera live view resolution change to %s:' % resolution,
        params = OrderedDict([('com','changelvqty'),('lvqty',resolution)])
        req = requests.get('http://' + OlympusAir.IP + '/exec_takemisc.cgi',headers=self.headers,params=params)
	req.raise_for_status()

	if (xmltodict.parse(req.text)['result'] == 'OK'):
            print 'OK'
        else:
            raise OlympusAirError(OlympusAirError.PREVIEW_RES_CHANGE)
        
        
        
        print 'Camera live view start:',
        params = OrderedDict([('com','startliveview'),('port',self.lvPort)])
        req = requests.get('http://' + OlympusAir.IP + '/exec_takemisc.cgi',headers=self.headers,params=params)
	req.raise_for_status()        
        print 'OK'
        
        
        
        data = self.lvSocket.recvfrom(128)

        if len(data) == 0:
            raise OlympusAirError(OlympusAirError.PREVIEW_DATA_UNAVAILABLE)
        
            
        
    def takePicture(self):
        print 'Camera picture acquisition:',
        params = OrderedDict([('com','newstarttake')])
        req = requests.get('http://' + OlympusAir.IP + '/exec_takemotion.cgi',headers=self.headers,params=params)
        req.raise_for_status()
      	print 'OK'
	
        
        eventIDs = [OlympusAirEvent.AUTO_FOCUS_RESULT,
		    OlympusAirEvent.READY_TO_CAPTURE,
		    OlympusAirEvent.CAPTURE_STARTED,
		    OlympusAirEvent.CAPTURE_FINISHED,
		    OlympusAirEvent.CAPTURE_PROCESS_FINISHED]
        ind, event = self.waitForEvent(eventIDs)

	# Raise an error if the camera could not focus
	if ind[0] == True and xmltodict.parse(event[0].data)['root']['result'] == 'ng':
		raise OlympusAirError(OlympusAirError.AF)
	
	# Raise an error if a capture was not finished
	if ind[3] == False:
		raise OlympusAirError(OlympusAirError.CAPTURE_FAILED)


	# for (i,j,k) in zip(eventIDs,ind,event):
        # 	print i,j,k
        
        
    def stopPreview(self):
        print 'Camera live view stop:',
        params = OrderedDict([('com','stopliveview')])
        req = requests.get('http://' + OlympusAir.IP + '/exec_takemisc.cgi',headers=self.headers,params=params)
        req.raise_for_status()
	print 'OK'
        
        if self.lvSocket != None:
        	self.lvSocket.close()
        

    def waitOnCardWrite(self):
	

	frame = OlympusAirLiveViewFrame()
	frame.getLiveViewFrame(self.lvSocket)

	nFrames = 0
	while frame.cardWriteInProgress == 0 and nFrames < 1000:
		frame.getLiveViewFrame(self.lvSocket)
		nFrames = nFrames + 1
		# print 'Write not started, getting frame %i/%i' % (nFrames,1000)

	nFrames = 0
	while frame.cardWriteInProgress == 1 and nFrames < 1000:
		frame.getLiveViewFrame(self.lvSocket)
		if nFrames == 0:
			print frame
			frame.showImage()
		nFrames = nFrames + 1
		# print 'Write started, getting frame %i/%i' % (nFrames,1000)

	