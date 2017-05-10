import os

from perforce.version import __version__
from perforce.GUI.Qt import QtCore, QtGui, QtWidgets
from perforce.AppInterop.BaseInterop import BaseInterop


class TestInterop(BaseInterop):
    window = None

    @staticmethod
    def setupTestingEnvironment():
        app = QtWidgets.QApplication([])

        TestInterop.window = QtWidgets.QWidget()
        return TestInterop.window, app

    @staticmethod
    def main_parent_window():
        return TestInterop.window

    @staticmethod
    def getIconPath():
        cwd = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        iconpath = os.path.join(cwd, "../images/")
        return os.path.realpath(iconpath)

    @staticmethod
    def getSceneFiles():
        return []

    @staticmethod
    def getTempPath():
        return tempfile.gettempdir()

    @staticmethod
    def getCurrentSceneFile():
        raise NotImplementedError

    @staticmethod
    def openScene(filePath):
        raise NotImplementedError

    @staticmethod
    def closeWindow(ui):
        raise NotImplementedError

    @staticmethod
    def refresh():
        raise NotImplementedError


    def initializeMenu(self, entries):
        window = self.main_parent_window()
        vbox = QtWidgets.QVBoxLayout()
        window.setLayout(vbox)

        self.menu_bar = QtWidgets.QMenuBar()
        self.menu = self.menu_bar.addMenu('Perforce')
        vbox.addWidget(self.menu_bar)

    def addMenuDivider(self, label):
        self.menu.addSeparator()
       
    def addMenuLabel(self, label):
        self.menu.addAction(label)

    def addMenuSubmenu(self, label, icon, entries):
        # Save our current menu
        parent = self.menu
        self.menu = parent.addMenu(label)

        # Fill up the submenu
        self.fillMenu(entries)

        # Reset our current menu
        self.menu = parent


    def addMenuCommand(self, label, icon, command):
        self.menu.addAction(label, command)