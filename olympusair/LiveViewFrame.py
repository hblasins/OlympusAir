# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>


import requests
import socket
import xmltodict
import datetime

from collections import OrderedDict
from datetime import date
from struct import *


class LiveViewFrame:

	ISO_LOW = 0xFFFE
	AF_NA = 0
	AF_OK = 1
	AF_FAILED = 2

	def __init__(self):
		self.jpegSize = None
		self.afType = None
		self.afXcoord = None
		self.afYcoord = None
		self.afWidth = None
		self.afHeight = None
		self.cardNotFull = None
		self.cardProtected = None
		self.cardError = None
		self.cardWriteInProgress = None
		self.cardMounted = None
		self.orientation = None
		self.capacity = None
		self.shutterCurrNum = None
		self.shutterCurrDenom = None
		self.shutterMaxNum = None
		self.shutterMaxDenom = None
		self.shutterMinNum = None
		self.shutterMinDenom = None

		self.fNumberCurr = None
		self.fNumberMax = None
		self.fNumberMin = None
		self.iso = None
		self.isoAuto = None
		self.isoWarning = None
		self.focusMode = None
		self.zoomCurr = None
		self.zoomWide = None
		self.zoomTele = None
		self.expWarning = None
		self.meteringWarning = None



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
		res = res +  'Exposure warning: %i, metering warning: %i' % (self.expWarning, self.meteringWarning)
		return res
		

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
				self.decodeMeterWarning(subdata)
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
		self.orientation = -1
		if orient == 1:
			self.orientation = 0
		elif orient == 3:
			self.orientation = 180
		elif orient == 6:
			self.orientation = 90
		elif orient == 8:
			self.orientaion = 270
			

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
	
	def decodeMeterWarning(self,data):
		self.expWarning = unpack_from('!H',data[0:2])[0] == 1
		self.meteringWarning = unpack_from('!H',data[2:4])[0] == 1
		
		# print 'Exposure warning: %i, metering warning: %i' % (self.expWarning, self.meteringWarning)
	

