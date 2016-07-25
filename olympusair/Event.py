# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>


import requests
import socket
import xmltodict
import datetime

from collections import OrderedDict
from datetime import date
from struct import *


class Event:

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
    
