import os
import logging
import sys

import nuke
    
import perforce.GlobalVars
from perforce.version import __version__
from perforce.AppInterop.BaseInterop import BaseInterop, BaseCallbacks
from perforce.GUI.Qt import QtCore, QtGui, QtWidgets, __binding__


class NukeInterop(BaseInterop):
    @staticmethod
    def setupTestingEnvironment():
        pass

    @staticmethod
    def main_parent_window():
        """
        Get the main Nuke window as a QtGui.QMainWindow instance
        @return: QtGui.QMainWindow instance of the top level Nuke windows
        """
        return QtWidgets.QApplication.activeWindow()
  
    @staticmethod
    def getSettingsPath():
        return os.environ['Nuke_APP_DIR']

    @staticmethod
    def getIconPath():
        return os.environ['Nuke_APP_DIR'] + "/scripts/Perforce/images/"
    
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


    def initializeMenu(self, entries):
        try:
            # gMainWindow = NukeInterop.main_parent_window()
            gMainWindow = Nuke.mel.eval('$temp1=$gMainWindow')
        except RuntimeError as e:
            print e
            print 'Are you running in Batch Python?'
            gMainWindow = None

        try:
            print 'Initialising menu...'
            self.perforceMenu = cmds.menu("PerforceMenu", parent=gMainWindow, tearOff=True, label='Perforce')
            cmds.setParent(self.perforceMenu, menu=True)
        except RuntimeError as e:
            print 'Nuke error while trying to create menu:',
            print e

    def addMenuDivider(self, label):
        try:
            cmds.menuItem(divider=True, label=label)
        except RuntimeError as e:
            print 'Nuke error while trying to create divider:',
            print e
       
    def addMenuLabel(self, label):
        try:
            cmds.menuItem(label=label, en=False)
        except RuntimeError as e:
            print 'Nuke error while trying to add menu entry:',
            print e

    def addMenuSubmenu(self, label, icon, entries):
        try:
            cmds.menuItem(subMenu=True, tearOff=False, label=label, image=icon)
        except RuntimeError as e:
            print 'Nuke error while trying to create submenu:',
            print e

        self.fillMenu(entries)

        try:
            cmds.setParent('..', menu=True )
        except RuntimeError as e:
            print 'Nuke error while trying to change menu parent:',
            print e

    def addMenuCommand(self, label, icon, command):
        try:
            cmds.menuItem( label=label, image=icon, command=command )
        except RuntimeError as e:
            print 'Nuke error while trying to change menu parent:',
            print e
import os
import logging
import sys

try:
    import Nuke.standalone
    Nuke.standalone.initialize()
except:
    pass

import Nuke.mel as mel
# import Nuke.utils as mu
import Nuke.cmds as cmds
import Nuke.OpenNukeUI as omui
try:
    from shiboken import wrapInstance
except ImportError:
    from shiboken2 import wrapInstance
    
import Nuke.OpenNuke as api

import perforce.GlobalVars
from perforce.version import __version__
from perforce.AppInterop.BaseInterop import BaseInterop, BaseCallbacks
from perforce.GUI.Qt import QtCore, QtGui, QtWidgets, __binding__

class NukeCallbacks(BaseCallbacks):
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



class NukeInterop(BaseInterop):
    @staticmethod
    def setupTestingEnvironment():
        import Nuke.standalone
        Nuke.standalone.initialize("Python")

    @staticmethod
    def main_parent_window():
        """
        Get the main Nuke window as a QtGui.QMainWindow instance
        @return: QtGui.QMainWindow instance of the top level Nuke windows
        """
        
        import Nuke.OpenNukeUI as apiUI
        if __binding__ in ('PySide2', 'PyQt5'):
            import shiboken2 as shiboken
        else:
            import shiboken
        
        ptr = apiUI.MQtUtil.mainWindow()
        if ptr is not None:
            return shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)
  
    @staticmethod
    def getSettingsPath():
        return os.environ['Nuke_APP_DIR']

    @staticmethod
    def getIconPath():
        return os.environ['Nuke_APP_DIR'] + "/scripts/Perforce/images/"
    
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


    def initializeMenu(self, entries):
        try:
            # gMainWindow = NukeInterop.main_parent_window()
            gMainWindow = Nuke.mel.eval('$temp1=$gMainWindow')
        except RuntimeError as e:
            print e
            print 'Are you running in Batch Python?'
            gMainWindow = None

        try:
            print 'Initialising menu...'
            self.perforceMenu = cmds.menu("PerforceMenu", parent=gMainWindow, tearOff=True, label='Perforce')
            cmds.setParent(self.perforceMenu, menu=True)
        except RuntimeError as e:
            print 'Nuke error while trying to create menu:',
            print e

    def addMenuDivider(self, label):
        try:
            cmds.menuItem(divider=True, label=label)
        except RuntimeError as e:
            print 'Nuke error while trying to create divider:',
            print e
       
    def addMenuLabel(self, label):
        try:
            cmds.menuItem(label=label, en=False)
        except RuntimeError as e:
            print 'Nuke error while trying to add menu entry:',
            print e

    def addMenuSubmenu(self, label, icon, entries):
        try:
            cmds.menuItem(subMenu=True, tearOff=False, label=label, image=icon)
        except RuntimeError as e:
            print 'Nuke error while trying to create submenu:',
            print e

        self.fillMenu(entries)

        try:
            cmds.setParent('..', menu=True )
        except RuntimeError as e:
            print 'Nuke error while trying to change menu parent:',
            print e

    def addMenuCommand(self, label, icon, command):
        try:
            cmds.menuItem( label=label, image=icon, command=command )
        except RuntimeError as e:
            print 'Nuke error while trying to change menu parent:',
            print e
