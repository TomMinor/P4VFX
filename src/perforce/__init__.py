try:
	from P4 import P4, P4Exception
except ImportError as e:
	print e
	print 'Ensure P4API is installed into your DCC script paths'
	raise e

import logging
logging.basicConfig(level=logging.INFO)

import DCCInterop
reload(DCCInterop)

import GUI
reload(GUI)

def init():
	GUI.init()

def close():
    GUI.close()
