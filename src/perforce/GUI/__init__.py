import os
import re
import traceback
import logging
import platform
from distutils.version import StrictVersion

from P4 import P4, P4Exception, Progress, OutputHandler

import perforce.Utils as Utils
import PerforceMenu
from perforce.AppInterop import interop

# try:
#     AppUtils.closeWindow(ui.perforceMenu)
# except:
#     ui = None

def initMenu(p4):
    global ui
    # try:
    #     # cmds.deleteUI(ui.perforceMenu)
    #     AppUtils.closeWindow(ui.perforceMenu)
    # except:
    #     pass

    # interop.initCallbacks()

    try:
        ui = PerforceMenu.MainShelf(p4)

        ui.addMenu()
    except ValueError as e:
        Utils.p4Logger().critical(e)

    # mu.executeDeferred('ui.addMenu()')


def cleanupMenu():
    global ui

    # interop.cleanupCallbacks()

    # try:
    #     # cmds.deleteUI(ui.perforceMenu)
    #     AppUtils.closeWindow(ui.perforceMenu)
    # except Exception as e:
    #     raise e

    ui.close()

    #del ui