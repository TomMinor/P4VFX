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
    try:
        p4.connect()
    except P4Exception as e:
        raise

    try:
        p4.run('info')
    except P4Exception as e:
        try:
            GUI.LoginWindow.setupConnection(p4)
        except P4Exception as e:
            raise

    if p4.p4config_file == 'noconfig':
        Utils.loadP4Config(p4)

    GUI.initMenu(p4)

def close():
    p4.disconnect()

    GUI.cleanupMenu()
