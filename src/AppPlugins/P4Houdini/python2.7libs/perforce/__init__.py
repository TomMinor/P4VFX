import os
# Allow the user to override P4CONFIG with their own name or absolute path
# But by default look for a .p4config file anywhere above the current working dir
if not os.getenv('P4CONFIG'):
    os.environ['P4CONFIG'] = '.p4config'

try:
    from P4 import P4, P4Exception
except ImportError as e:
    raise ImportError('%s, ensure P4API is installed into your DCC script paths' % e)

import logging
logging.basicConfig(
    format = "%(levelname) -10s %(asctime)s %(module)s:%(lineno)s %(funcName)s %(message)s",
    level = logging.DEBUG
)

from PerforceUtils import SetupConnection
reload(SetupConnection)

import GUI
reload(GUI)


# Evil global
p4 = P4()

def init():
    # Everything relies on the P4 environment being setup, so don't even try and load if it's not set properly
    # if p4.p4config_file == 'noconfig':
    #     raise RuntimeError("Can't find P4CONFIG, please ensure your Perforce is set correctly. (Look at 'p4 set' and set the P4CONFIG environment variable to the location of your configuration file")

    GUI.initMenu(p4)

def close():
    p4.disconnect()

    GUI.cleanupMenu()
