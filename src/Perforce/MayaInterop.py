import os
import logging
import sys

import maya.mel as mel
# import maya.utils as mu
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken import wrapInstance

from PySide import QtCore
from PySide import QtGui

import GlobalVars
from Version import __version__
from BaseInterop import BaseInterop



class MayaInterop(BaseInterop):
    @staticmethod
    def setupTestingEnvironment():
        import maya.standalone
        maya.standalone.initialize("Python")
        print os.environ["MAYA_SCRIPT_PATH"]

    @staticmethod
    def main_parent_window():
        """
        Get the main Maya window as a QtGui.QMainWindow instance
        @return: QtGui.QMainWindow instance of the top level Maya windows
        """
        try:
            window = mel.eval('$temp1=$gMainWindow')
            return window
        except RuntimeError as e:
            print e
        
        return None
        # main_window_ptr = omui.MQtUtil.mainWindow()
        # if main_window_ptr:
        #     return wrapInstance(long(main_window_ptr), QtGui.QWidget)
        # else:
        #     return None

    @staticmethod
    def createMenu(entries):
        try:
            gMainWindow = MayaInterop.main_parent_window()
        except RuntimeError as e:
            print e
            print 'Are you running in Batch Python?'
            gMainWindow = None

        try:
            print 'Initialising menu...'
            perforceMenu = cmds.menu("PerforceMenu", parent=gMainWindow, tearOff=True, label='Perforce')
            cmds.setParent(perforceMenu, menu=True)
            batchmode = False
        except RuntimeError as e:
            print 'Maya error while trying to create menu:',
            print e
            batchmode = True

        def fillMenu(entries, debugPrint=False, indent=0):
            if debugPrint:
                debugIndent = '\t' * indent

            for entry in entries:
                if entry.get('divider'):
                    # Create divider
                    if debugPrint:
                        print debugIndent,
                        if entry.get('label'):
                            print entry['label'],
                        print '-'*50

                    try:
                        cmds.menuItem(divider=True, label=entry.get('label'))
                    except RuntimeError as e:
                        print 'Maya error while trying to create divider:',
                        print e

                elif entry.get('entries'):
                    # Create submenu
                    if debugPrint:
                        print debugIndent,
                        print '>>>',
                        if entry.get('label'):
                            print entry['label']

                    try:
                        cmds.menuItem(subMenu=True, tearOff=False, label=entry.get('label'), image=entry.get('image'))
                    except RuntimeError as e:
                        print 'Maya error while trying to create submenu:',
                        print e

                    fillMenu( entry['entries'], debugPrint, indent+1)

                    try:
                        cmds.setParent('..', menu=True )
                    except RuntimeError as e:
                        print 'Maya error while trying to change menu parent:',
                        print e
                elif entry.get('command'):
                    # Add an entry
                    if debugPrint:
                        print debugIndent,
                        print '|' + entry.get('label')

                    try:
                        cmds.menuItem(  label=entry.get('label'),
                                        image=entry.get('image'),
                                        command=entry.get('command') )
                    except RuntimeError as e:
                        print 'Maya error while trying to change menu parent:',
                        print e
                else:
                    raise ValueError('Unknown entry type')
            
            # Add a readonly version entry
            if debugPrint:
                print debugIndent,
                print '|' + __version__
            try:
                cmds.menuItem(label="Version {0}".format(__version__), en=False)
            except RuntimeError as e:
                print 'Maya error while trying to add menu entry:',
                print e

        fillMenu(entries, debugPrint=batchmode)

    @staticmethod
    def getIconPath():
        return os.environ['MAYA_APP_DIR'] + "/scripts/Perforce/images/"
    
    @staticmethod
    def getSceneFiles():
        return ['.ma', '.mb']
    
    # @staticmethod
    # def getTempPath():
        # return os.environ['TMPDIR']

    @staticmethod
    def getCurrentSceneFile():
        return cmds.file(q=True, sceneName=True)


    @staticmethod
    def openScene(filePath):
        cmds.file(filePath, f=True, o=True)


    @staticmethod
    def closeWindow(ui):
        cmds.deleteUI(ui)


    @staticmethod
    def refresh():
        cmds.refresh()

