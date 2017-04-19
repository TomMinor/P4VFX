import os
import logging
import sys

try:
    import maya.standalone
    maya.standalone.initialize()
except:
    pass

import maya.mel as mel
# import maya.utils as mu
import maya.cmds as cmds
import maya.OpenMayaUI as omui
try:
    from shiboken import wrapInstance
except ImportError:
    from shiboken2 import wrapInstance
    
import maya.OpenMaya as api

import GlobalVars
from version import __version__
from BaseInterop import BaseInterop, BaseCallbacks
from perforce.GUI.Qt import QtCore, QtGui, QtWidgets

class MayaCallbacks(BaseCallbacks):
    contactrootenv = "CONTACTROOT"
    referenceCallback = None
    saveCallback = None

    def validateSubmit():
        print "Validating submission"
        return 0

    def cleanupCallbacks():
        if referenceCallback:
            try:
                api.MCommandMessage.removeCallback(referenceCallback)
            except RuntimeError as e:
                print e

        if saveCallback:
            try:
                api.MCommandMessage.removeCallback(saveCallback)
            except RuntimeError as e:
                print e


    def initCallbacks():
        cleanupCallbacks()

        referenceCallback = api.MSceneMessage.addCheckFileCallback(
            api.MSceneMessage.kBeforeCreateReferenceCheck,
            referenceCallbackFunc)

        saveCallback = api.MSceneMessage.addCallback(
            api.MSceneMessage.kAfterSave,
            saveCallbackFunc)


    def saveCallbackFunc(*args):
        fileName = cmds.file(q=True, sceneName=True)

        if ".ma" in fileName:
            print "Save callback: Checking file {0} for education flags".format(fileName)
            Utils.removeStudentTag(fileName)

    def referenceCallbackFunc(inputBool, inputFile, *args):
        api.MScriptUtil.getBool(inputBool)

        print "Reference callback: Checking file {0}".format(os.environ[contactrootenv])

        try:
            contactrootpath = os.environ[contactrootenv]
        except KeyError as e:
            print "Error", e
            api.MScriptUtil.setBool(inputBool, True)
            return

        rawpath = inputFile.rawPath()
        rawname = inputFile.rawName()
        oldpath = rawpath
        if contactrootpath in rawpath:
            rawpath = rawpath.replace(
                contactrootpath, "${0}".format(contactrootenv))
            inputFile.setRawPath(rawpath)
            print "Remapped {0} -> {1}".format(oldpath, rawpath)

        if contactrootenv in rawpath:
            resolvedName = os.path.join(rawpath.replace("${0}".format(contactrootenv), contactrootpath), rawname)
            print rawpath, "->", resolvedName
            inputFile.overrideResolvedFullName(resolvedName)

        # print "RAWPATH", inputFile.rawPath()
        # print "RAWFULLNAME", inputFile.rawFullName()
        # print "RAWEXPANDEDPATH", inputFile.expandedPath()

        api.MScriptUtil.setBool(inputBool, True)



class MayaInterop(BaseInterop):
    @staticmethod
    def setupTestingEnvironment():
        import maya.standalone
        maya.standalone.initialize("Python")

    @staticmethod
    def main_parent_window():
        """
        Get the main Maya window as a QtGui.QMainWindow instance
        @return: QtGui.QMainWindow instance of the top level Maya windows
        """
        # try:
        #     window = mel.eval('$temp1=$gMainWindow')
        #     return window
        # except RuntimeError as e:
        #     print e
        
        # return None
        main_window_ptr = omui.MQtUtil.mainWindow()
        if main_window_ptr:
            return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)
        else:
            return None

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

        def fillMenu(entries):
            for entry in entries:
                if entry.get('divider'):
                    try:
                        cmds.menuItem(divider=True, label=entry.get('label'))
                    except RuntimeError as e:
                        print 'Maya error while trying to create divider:',
                        print e

                elif entry.get('entries'):
                    try:
                        cmds.menuItem(subMenu=True, tearOff=False, label=entry.get('label'), image=entry.get('image'))
                    except RuntimeError as e:
                        print 'Maya error while trying to create submenu:',
                        print e

                    fillMenu( entry['entries'] )

                    try:
                        cmds.setParent('..', menu=True )
                    except RuntimeError as e:
                        print 'Maya error while trying to change menu parent:',
                        print e
                elif entry.get('command'):
                    try:
                        cmds.menuItem(  label=entry.get('label'),
                                        image=entry.get('image'),
                                        command=entry.get('command') )
                    except RuntimeError as e:
                        print 'Maya error while trying to change menu parent:',
                        print e
                else:
                    raise ValueError('Unknown entry type')
            
            try:
                cmds.menuItem(label="Version {0}".format(__version__), en=False)
            except RuntimeError as e:
                print 'Maya error while trying to add menu entry:',
                print e

        fillMenu(entries)

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

