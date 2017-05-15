try:
    from P4 import P4, P4Exception
except ImportError as e:
    raise ImportError('%s, ensure P4API is installed into your DCC script paths' % e)

import logging
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

import Utils
reload(Utils)

import GUI
reload(GUI)


# Evil global
p4 = P4()

def init():
    Utils.setupConnection(p4)

    GUI.initMenu(p4)

def close():
    p4.disconnect()

    GUI.cleanupMenu()
