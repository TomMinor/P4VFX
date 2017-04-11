try:
	from P4 import P4, P4Exception
except ImportError as e:
	print e
	print 'Ensure P4API is installed into your DCC script paths'
	raise e

import AppUtils

if __name__ == '__main__':
	AppUtils.Utils.setupTestingEnvironment()

import GUI
reload(GUI)

def init():
	GUI.init()

def close():
    GUI.close()
