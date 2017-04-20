try:
	from P4 import P4, P4Exception
except ImportError as e:
	raise ImportError('%s, ensure P4API is installed into your DCC script paths' % e)

import logging
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

import GUI
reload(GUI)

def init():
	GUI.init()

def close():
    GUI.close()
