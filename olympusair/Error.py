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

class Error(Exception):

	AF = 0
	PROPERTY_NOT_CHANGED = 1
	CAPTURE_FAILED = 2
	PREVIEW_RES_CHANGE = 3
	PREVIEW_DATA_UNAVAILABLE = 4

	def __init__(self,value):
		self.value = value

	def __str__(self):
		return 'OlympusAir error'

