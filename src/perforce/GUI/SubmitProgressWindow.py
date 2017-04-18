from P4 import P4, P4Exception

from PySide import QtCore
from PySide import QtGui

import perforce.Utils as Utils

class SubmitProgressUI(QtGui.QDialog):

    def __init__(self, totalFiles, parent=mainParent):
        super(SubmitProgressUI, self).__init__(parent)
        self.handler = None

        self.totalFiles = totalFiles

        self.currentFile = 0

    def setHandler(self, handler):
        self.handler = handler

    def setMaximum(self, val):
        self.fileProgressBar.setMaximum(val)

    def setMinimum(self, val):
        self.fileProgressBar.setMinimum(val)

    def setValue(self, val):
        self.fileProgressBar.setValue(val)

    def incrementCurrent(self):
        self.currentFile += 1
        self.overallProgressBar.setValue(self.currentFile)

        print self.totalFiles, self.currentFile

        if self.currentFile >= self.totalFiles:
            setComplete(True)

    def setComplete(self, success):
        if not success:
            self.overallProgressBar.setTextVisible(True)
            self.overallProgressBar.setFormat("Cancelled/Error")

            self.fileProgressBar.setTextVisible(True)
            self.fileProgressBar.setFormat("Cancelled/Error")

        self.quitBtn.setText("Quit")

    def create(self, title, files=[]):
        path = iconPath + "p4.png"
        icon = QtGui.QIcon(path)

        self.setWindowTitle(title)
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.Dialog)

        self.create_controls()
        self.create_layout()
        self.create_connections()

    def create_controls(self):
        '''
        Create the widgets for the dialog
        '''

        self.overallProgressBar = QtGui.QProgressBar()
        self.overallProgressBar.setMinimum(0)
        self.overallProgressBar.setMaximum(self.totalFiles)
        self.overallProgressBar.setValue(0)

        self.fileProgressBar = QtGui.QProgressBar()
        self.fileProgressBar.setMinimum(0)
        self.fileProgressBar.setMaximum(100)
        self.fileProgressBar.setValue(0)

        self.quitBtn = QtGui.QPushButton("Cancel")

    def create_layout(self):
        '''
        Create the layouts and add widgets
        '''
        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)

        formlayout1 = QtGui.QFormLayout()
        formlayout1.addRow("Total Progress:", self.overallProgressBar)
        formlayout1.addRow("File Progress:", self.fileProgressBar)

        main_layout.addLayout(formlayout1)
        main_layout.addWidget(self.quitBtn)
        self.setLayout(main_layout)

    def create_connections(self):
        '''
        Create the signal/slot connections
        '''
        # self.fileTree.clicked.connect( self.loadFileLog )
        self.quitBtn.clicked.connect(self.cancelProgress)

    #--------------------------------------------------------------------------
    # SLOTS
    #--------------------------------------------------------------------------

    def cancelProgress(self, *args):
        self.quitBtn.setText("Cancelling...")
        self.handler.setCancel(True)