import os

from perforce.version import __version__
from perforce.GUI.Qt import QtCore, QtGui, QtWidgets
from perforce.AppInterop.BaseInterop import BaseInterop


from PySide import QtCore
from PySide import QtGui

class TestInterop(BaseInterop):
    window = None

    @staticmethod
    def setupTestingEnvironment():
        app = QtWidgets.QApplication([])

        TestInterop.window = QtWidgets.QLabel('Test')
        TestInterop.window.show()
        return app

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
        return None

    def addMenuDivider(self, label):
        print label
        print '-'*50
       
    def addMenuLabel(self, label):
        print '|' + label

    def addMenuSubmenu(self, label, icon, entries):
        print '>>>',
        print label

        self.fillMenu(entries)

    def addMenuCommand(self, label, icon, command):
        print '|' + label