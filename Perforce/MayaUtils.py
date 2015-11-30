import os
import logging

import maya.mel
import maya.utils as mu
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken import wrapInstance

from PySide import QtCore
from PySide import QtGui

import GlobalVars
reload(GlobalVars)

p4_logger = logging.getLogger("Perforce")

# Hacky way to load our icons, I don't fancy wrestling with resource files
GlobalVars.iconPath = os.environ['MAYA_APP_DIR'] + "/scripts/Perforce/images/"
print GlobalVars.iconPath

def main_parent_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)

def getCurrentSceneFile():
    return cmds.file(q=True, sceneName=True)
    
def openScene(filePath):
    cmds.file(filePath, f=True, o=True)
