import os
import sys
import re
import logging

from P4 import P4, P4Exception

p4_logger = logging.getLogger("Perforce")

import Utils
reload(Utils)

import AppUtils
reload(AppUtils)

import GlobalVars
reload(GlobalVars)

GlobalVars.tempPath = os.environ['TMPDIR']

class P4Icon:
	iconName = "p4.png"
	addFile = "File0242.png"    
	editFile = "File0440.png"
	deleteFile = "File0253.png"

GlobalVars.P4Icon = P4Icon

import GUI
reload(GUI)

def init():
	GUI.init()

def close():
	GUI.close()