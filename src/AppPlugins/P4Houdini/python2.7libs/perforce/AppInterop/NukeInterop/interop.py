import os
import logging
import sys
import platform

import nuke
    
import perforce.GlobalVars
from perforce import Utils
from perforce.version import __version__
from perforce.AppInterop.BaseInterop import BaseInterop, BaseCallbacks
from perforce.GUI.qtpy import QtCore, QtGui, QtWidgets


class NukeInterop(BaseInterop):
    @staticmethod
    def setupEnvironment():
        pass

    @staticmethod
    def main_parent_window():
        return None
        # return QtWidgets.QApplication.activeWindow()
  
    @staticmethod
    def getSettingsPath():
        if platform.system() == 'Windows':
            if os.environ.get('HOME'):
                home = os.environ['HOME']
            else:
                home = os.environ['USERPROFILE']
            return os.path.join(home, '.nuke')

        elif platform.system() == 'Linux':
            return os.path.expanduser('~/.nuke')

        elif platform.system() == 'Darwin':
            return os.path.expanduser('~/.nuke')

    @staticmethod
    def getIconPath():
        return os.path.join(NukeInterop.getSettingsPath(), "P4Nuke", "perforce", "images")
    
    @staticmethod
    def getSceneFiles():
        return ['.nk']
    
    @staticmethod
    def getTempPath():
        return os.environ['NUKE_TEMP_DIR']

    @staticmethod
    def getCurrentSceneFile():
        return nuke.root().name()


    @staticmethod
    def openScene(filePath):
        nuke.scriptOpen(filePath)


    @staticmethod
    def closeWindow(ui):
        pass


    @staticmethod
    def refresh():
        nuke.updateUI()


    # Nuke doesn't like absolute icons for it's menus,
    # so strip out the filename only and ignore the path
    def sanitizeIconPath(self, iconPath):
        return os.path.basename(iconPath)
    
    def initializeMenu(self, entries):
        m = nuke.menu( 'Nuke' )
        self.menu = m.addMenu( 'Perforce' )

    def addMenuDivider(self, label):
        self.menu.addSeparator()
       
    def addMenuLabel(self, label):
        tmp = self.menu.addCommand(label, lambda: None)
        tmp.setEnabled(False)

    def addMenuSubmenu(self, label, iconPath, entries):
        # Save our current menu
        parent = self.menu
        self.menu = parent.addMenu(label, icon=self.sanitizeIconPath(iconPath))

        # Fill up the submenu
        self.fillMenu(entries)

        # Reset our current menu
        self.menu = parent


    def addMenuCommand(self, label, iconPath, command):
        self.menu.addCommand(label, command, icon=self.sanitizeIconPath(iconPath))