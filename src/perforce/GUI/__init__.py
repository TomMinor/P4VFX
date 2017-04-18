import os
import re
import traceback
import logging
import platform
from distutils.version import StrictVersion

from P4 import P4, P4Exception, Progress, OutputHandler

import perforce.Utils as Utils
import perforce.AppUtils as AppUtils
import perforce.Callbacks as Callbacks
import PerforceMenu

# try:
#     AppUtils.closeWindow(ui.perforceMenu)
# except:
#     ui = None

def init():
    global ui
    # try:
    #     # cmds.deleteUI(ui.perforceMenu)
    #     AppUtils.closeWindow(ui.perforceMenu)
    # except:
    #     pass

    p4 = P4()
    if p4.p4config_file == 'noconfig':
        Utils.loadP4Config(p4)

    Callbacks.initCallbacks()

    try:
        ui = PerforceMenu.PerforceUI(p4)

        ui.addMenu()
    except ValueError as e:
        Utils.p4Logger().critical(e)

    # mu.executeDeferred('ui.addMenu()')


def close():
    global ui

    Callbacks.cleanupCallbacks()

    # try:
    #     # cmds.deleteUI(ui.perforceMenu)
    #     AppUtils.closeWindow(ui.perforceMenu)
    # except Exception as e:
    #     raise e

    ui.close()

    #del ui