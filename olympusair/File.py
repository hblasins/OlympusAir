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
from StringIO import StringIO


    
class File:
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
        
