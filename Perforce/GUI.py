import os
import re
import traceback
import logging
import platform
from distutils.version import StrictVersion

from PySide import QtCore
from PySide import QtGui

from P4 import P4, P4Exception, Progress, OutputHandler

import Utils
import AppUtils
import GlobalVars
import Callbacks

reload(Utils)
reload(AppUtils)
reload(GlobalVars)
reload(Callbacks)


version = '1.1.3'


mainParent = AppUtils.main_parent_window()

iconPath = GlobalVars.iconPath
tempPath = GlobalVars.tempPath
P4Icon = GlobalVars.P4Icon
sceneFiles = GlobalVars.sceneFiles

p4_logger = logging.getLogger("Perforce")


def displayErrorUI(e):
    error_ui = QtGui.QMessageBox()
    error_ui.setWindowFlags(QtCore.Qt.WA_DeleteOnClose)

    eMsg, type = Utils.parsePerforceError(e)

    if type == "warning":
        error_ui.warning(mainParent, "Perforce Warning", eMsg)
    elif type == "error":
        error_ui.critical(mainParent, "Perforce Error", eMsg)
    else:
        error_ui.information(mainParent, "Perforce Error", eMsg)

    error_ui.deleteLater()


class TestOutputAndProgress(Progress, OutputHandler):

    def __init__(self, ui):
        Progress.__init__(self)
        OutputHandler.__init__(self)
        self.totalFiles = 0
        self.totalSizes = 0
        self.ui = ui
        self.ui.setMinimum(0)
        self.ui.setHandler(self)

        self.shouldCancel = False

    def setCancel(self, val):
        self.shouldCancel = val

    def outputStat(self, stat):
        if 'totalFileCount' in stat:
            self.totalFileCount = int(stat['totalFileCount'])
            print "TOTAL FILE COUNT: ", self.totalFileCount
        if 'totalFileSize' in stat:
            self.totalFileSize = int(stat['totalFileSize'])
            print "TOTAL FILE SIZE: ", self.totalFileSize
        if self.shouldCancel:
            return OutputHandler.REPORT | OutputHandler.CANCEL
        else:
            return OutputHandler.HANDLED

    def outputInfo(self, info):
        AppUtils.refresh()
        print "INFO :", info
        if self.shouldCancel:
            return OutputHandler.REPORT | OutputHandler.CANCEL
        else:
            return OutputHandler.HANDLED

    def outputMessage(self, msg):
        AppUtils.refresh()
        print "Msg :", msg

        if self.shouldCancel:
            return OutputHandler.REPORT | OutputHandler.CANCEL
        else:
            return OutputHandler.HANDLED

    def init(self, type):
        AppUtils.refresh()
        print "Begin :", type
        self.type = type
        self.ui.incrementCurrent()

    def setDescription(self, description, unit):
        AppUtils.refresh()
        print "Desc :", description, unit
        pass

    def setTotal(self, total):
        AppUtils.refresh()
        print "Total :", total
        self.ui.setMaximum(total)
        pass

    def update(self, position):
        AppUtils.refresh()
        print "Update : ", position
        self.ui.setValue(position)
        self.position = position

    def done(self, fail):
        AppUtils.refresh()
        print "Failed :", fail
        self.fail = fail


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

#


class SubmitChangeUi(QtGui.QDialog):

    def __init__(self, parent=mainParent):
        super(SubmitChangeUi, self).__init__(parent)

    def create(self, p4, files=[]):
        self.p4 = p4

        path = iconPath + P4Icon.iconName
        icon = QtGui.QIcon(path)

        self.setWindowTitle("Submit Change")
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.Window)

        self.fileList = files

        self.create_controls()
        self.create_layout()
        self.create_connections()

        self.validateText()

    def create_controls(self):
        '''
        Create the widgets for the dialog
        '''
        self.submitBtn = QtGui.QPushButton("Submit")
        self.descriptionWidget = QtGui.QPlainTextEdit("<Enter Description>")
        self.descriptionLabel = QtGui.QLabel("Change Description:")
        self.chkboxLockedWidget = QtGui.QCheckBox("Keep files checked out?")

        headers = [" ", "File", "Type", "Action", "Folder"]

        self.tableWidget = QtGui.QTableWidget(len(self.fileList), len(headers))
        self.tableWidget.setMaximumHeight(200)
        self.tableWidget.setMinimumWidth(500)
        self.tableWidget.setHorizontalHeaderLabels(headers)

        for i, file in enumerate(self.fileList):
            # Saves us manually keeping track of the current column
            column = 0

            # Create checkbox in first column
            widget = QtGui.QWidget()
            layout = QtGui.QHBoxLayout()
            chkbox = QtGui.QCheckBox()
            chkbox.setCheckState(QtCore.Qt.Checked)

            layout.addWidget(chkbox)
            layout.setAlignment(QtCore.Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(layout)

            self.tableWidget.setCellWidget(i, column, widget)
            column += 1

            # Fill in the rest of the data
            # File
            fileName = file['File']
            newItem = QtGui.QTableWidgetItem(os.path.basename(fileName))
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

            # Text
            fileType = file['Type']
            newItem = QtGui.QTableWidgetItem(fileType.capitalize())
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

            # Pending Action
            pendingAction = file['Pending_Action']

            path = ""
            if(pendingAction == "edit"):
                path = os.path.join(iconPath, P4Icon.editFile)
            elif(pendingAction == "add"):
                path = os.path.join(iconPath, P4Icon.addFile)
            elif(pendingAction == "delete"):
                path = os.path.join(iconPath, P4Icon.deleteFile)

            widget = QtGui.QWidget()

            icon = QtGui.QPixmap(path)
            icon = icon.scaled(16, 16)

            iconLabel = QtGui.QLabel()
            iconLabel.setPixmap(icon)
            textLabel = QtGui.QLabel(pendingAction.capitalize())

            layout = QtGui.QHBoxLayout()
            layout.addWidget(iconLabel)
            layout.addWidget(textLabel)
            layout.setAlignment(QtCore.Qt.AlignLeft)
            # layout.setContentsMargins(0,0,0,0)
            widget.setLayout(layout)

            self.tableWidget.setCellWidget(i, column, widget)
            column += 1

            # Folder
            newItem = QtGui.QTableWidgetItem(file['Folder'])
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setStretchLastSection(True)

    def create_layout(self):
        '''
        Create the layouts and add widgets
        '''
        check_box_layout = QtGui.QHBoxLayout()
        check_box_layout.setContentsMargins(2, 2, 2, 2)

        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)

        main_layout.addWidget(self.descriptionLabel)
        main_layout.addWidget(self.descriptionWidget)
        main_layout.addWidget(self.tableWidget)

        main_layout.addWidget(self.chkboxLockedWidget)
        main_layout.addWidget(self.submitBtn)

        # main_layout.addStretch()

        self.setLayout(main_layout)

    def create_connections(self):
        '''
        Create the signal/slot connections
        '''
        self.submitBtn.clicked.connect(self.on_submit)
        self.descriptionWidget.textChanged.connect(self.on_text_changed)

    # --------------------------------------------------------------------------
    # SLOTS
    # --------------------------------------------------------------------------
    def on_submit(self):
        if not self.validateText():
            QtGui.QMessageBox.warning(
                mainParent, "Submit Warning", "No valid description entered")
            return

        files = []
        for i in range(self.tableWidget.rowCount()):
            cellWidget = self.tableWidget.cellWidget(i, 0)
            if cellWidget.findChild(QtGui.QCheckBox).checkState() == QtCore.Qt.Checked:
                files.append(self.fileList[i]['File'])

        keepCheckedOut = self.chkboxLockedWidget.checkState()

        progress = SubmitProgressUI(len(files))
        progress.create("Submit Progress")

        callback = TestOutputAndProgress(progress)

        progress.show()

        # self.p4.progress = callback
        # self.p4.handler = callback

        # Remove student setting from .ma
        for submitFile in files:
            if ".ma" in submitFile:
                try:
                    pathData = self.p4.run_where(submitFile)[0]
                    Utils.removeStudentTag(pathData['path'])
                except P4Exception as e:
                    print e


        try:
            Utils.submitChange(self.p4, files, str(
                self.descriptionWidget.toPlainText()), callback, keepCheckedOut)
            if not keepCheckedOut:
                clientFiles = []
                for file in files:
                    try:
                        path = self.p4.run_fstat(file)[0]
                        clientFiles.append(path['clientFile'])
                    except P4Exception as e:
                        displayErrorUI(e)

                # Bug with windows, doesn't make files writable on submit for
                # some reason
                Utils.removeReadOnlyBit(clientFiles)
            self.close()
        except P4Exception as e:
            self.p4.progress = None
            self.p4.handler = None
            displayErrorUI(e)

        progress.close()

        self.p4.progress = None
        self.p4.handler = None

    def validateText(self):
        text = self.descriptionWidget.toPlainText()
        p = QtGui.QPalette()
        if text == "<Enter Description>" or "<" in text or ">" in text:
            p.setColor(QtGui.QPalette.Active,
                       QtGui.QPalette.Text, QtCore.Qt.red)
            p.setColor(QtGui.QPalette.Inactive,
                       QtGui.QPalette.Text, QtCore.Qt.red)
            self.descriptionWidget.setPalette(p)
            return False
        self.descriptionWidget.setPalette(p)
        return True

    def on_text_changed(self):
        self.validateText()


class OpenedFilesUI(QtGui.QDialog):

    def __init__(self, parent=mainParent):
        super(OpenedFilesUI, self).__init__(parent)

    def create(self, p4, files=[]):
        self.p4 = p4

        path = iconPath + P4Icon.iconName
        icon = QtGui.QIcon(path)

        self.setWindowTitle("Changelist : Opened Files")
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.Window)

        self.entries = []

        self.create_controls()
        self.create_layout()
        self.create_connections()

    def create_controls(self):
        '''
        Create the widgets for the dialog
        '''
        headers = ["File", "Type", "Action", "User", "Folder"]

        self.tableWidget = QtGui.QTableWidget(0, len(headers))
        self.tableWidget.setMaximumHeight(200)
        self.tableWidget.setMinimumWidth(500)
        self.tableWidget.setHorizontalHeaderLabels(headers)
        self.tableWidget.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(
            QtGui.QAbstractItemView.SingleSelection)

        self.openSelectedBtn = QtGui.QPushButton("Open")
        self.openSelectedBtn.setEnabled(False)
        self.openSelectedBtn.setIcon(QtGui.QIcon(
            os.path.join(iconPath, "File0228.png")))

        self.revertFileBtn = QtGui.QPushButton("Remove from changelist")
        self.revertFileBtn.setEnabled(False)
        self.revertFileBtn.setIcon(QtGui.QIcon(
            os.path.join(iconPath, "File0308.png")))

        self.refreshBtn = QtGui.QPushButton("Refresh")
        self.refreshBtn.setIcon(QtGui.QIcon(
            os.path.join(iconPath, "File0175.png")))

        self.updateTable()

    def create_layout(self):
        '''
        Create the layouts and add widgets
        '''
        check_box_layout = QtGui.QHBoxLayout()
        check_box_layout.setContentsMargins(2, 2, 2, 2)

        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)

        main_layout.addWidget(self.tableWidget)

        bottomLayout = QtGui.QHBoxLayout()
        bottomLayout.addWidget(self.revertFileBtn)
        bottomLayout.addWidget(self.refreshBtn)
        bottomLayout.addSpacerItem(QtGui.QSpacerItem(400, 16))
        bottomLayout.addWidget(self.openSelectedBtn)

        main_layout.addLayout(bottomLayout)

        self.setLayout(main_layout)

    def create_connections(self):
        '''
        Create the signal/slot connections
        '''
        self.revertFileBtn.clicked.connect(self.revertSelected)
        self.openSelectedBtn.clicked.connect(self.openSelectedFile)
        self.tableWidget.clicked.connect(self.validateSelected)
        self.refreshBtn.clicked.connect(self.updateTable)

    # --------------------------------------------------------------------------
    #  SLOTS
    # --------------------------------------------------------------------------
    def revertSelected(self, *args):
        index = self.tableWidget.currentRow()

        fileName = self.entries[index]['File']
        filePath = self.entries[index]['Folder']

        depotFile = os.path.join(filePath, fileName)

        try:
            p4_logger.info(self.p4.run_revert("-k", depotFile))
        except P4Exception as e:
            displayErrorUI(e)

        self.updateTable()

    def validateSelected(self, *args):
        index = self.tableWidget.currentRow()
        item = self.entries[index]
        fileName = item['File']
        filePath = item['Folder']

        depotFile = os.path.join(filePath, fileName)

        self.openSelectedBtn.setEnabled(True)

        self.revertFileBtn.setEnabled(True)

    def openSelectedFile(self, *args):
        index = self.tableWidget.currentRow()
        item = self.entries[index]
        fileName = item['File']
        filePath = item['Folder']

        depotFile = os.path.join(filePath, fileName)

        try:
            result = self.p4.run_fstat(depotFile)[0]
            clientFile = result['clientFile']

            if Utils.queryFileExtension(depotFile, ['.ma', '.mb']):
                AppUtils.openScene(clientFile)
            else:
                Utils.open_file(clientFile)
        except P4Exception as e:
            displayErrorUI(e)

    def updateTable(self):
        fileList = self.p4.run_opened(
            "-u", self.p4.user, "-C", self.p4.client, "...")

        self.entries = []
        for file in fileList:
            filePath = file['clientFile']
            #fileInfo = self.p4.run_fstat( filePath )[0]
            locked = 'ourLock' in file

            entry = {'File': filePath,
                     'Folder': os.path.split(filePath)[0],
                     'Type': file['type'],
                     'User': file['user'],
                     'Pending_Action': file['action'],
                     'Locked': locked
                     }

            self.entries.append(entry)

        self.tableWidget.setRowCount(len(self.entries))

        for i, file in enumerate(self.entries):
            # Saves us manually keeping track of the current column
            column = 0

            # Fill in the rest of the data
            # File
            fileName = file['File']
            newItem = QtGui.QTableWidgetItem(os.path.basename(fileName))
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

            # Text
            fileType = file['Type']
            newItem = QtGui.QTableWidgetItem(fileType.capitalize())
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

            # Pending Action
            pendingAction = file['Pending_Action']

            path = ""
            if(pendingAction == "edit"):
                path = os.path.join(iconPath, P4Icon.editFile)
            elif(pendingAction == "add"):
                path = os.path.join(iconPath, P4Icon.addFile)
            elif(pendingAction == "delete"):
                path = os.path.join(iconPath, P4Icon.deleteFile)

            widget = QtGui.QWidget()

            icon = QtGui.QPixmap(path)
            icon = icon.scaled(16, 16)

            iconLabel = QtGui.QLabel()
            iconLabel.setPixmap(icon)
            textLabel = QtGui.QLabel(pendingAction.capitalize())

            layout = QtGui.QHBoxLayout()
            layout.addWidget(iconLabel)
            layout.addWidget(textLabel)
            layout.setAlignment(QtCore.Qt.AlignLeft)
            # layout.setContentsMargins(0,0,0,0)
            widget.setLayout(layout)

            self.tableWidget.setCellWidget(i, column, widget)
            column += 1

            # User
            fileType = file['User']
            newItem = QtGui.QTableWidgetItem(fileType)
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

            # Folder
            newItem = QtGui.QTableWidgetItem(file['Folder'])
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setStretchLastSection(True)


# %TODO Implement my new method

class FileRevisionUI(QtGui.QDialog):

    def __init__(self, parent=mainParent):
        super(FileRevisionUI, self).__init__(parent)

    def create(self, p4, files=[]):
        self.p4 = p4

        path = iconPath + P4Icon.iconName
        icon = QtGui.QIcon(path)

        self.setWindowTitle("File Revisions")
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.Window)

        self.fileRevisions = []

        self.create_controls()
        self.create_layout()
        self.create_connections()

    def create_controls(self):
        '''
        Create the widgets for the dialog
        '''
        self.descriptionWidget = QtGui.QPlainTextEdit("<Enter Description>")
        self.descriptionLabel = QtGui.QLabel("Change Description:")
        self.getRevisionBtn = QtGui.QPushButton("Revert to Selected Revision")
        self.getLatestBtn = QtGui.QPushButton("Sync to Latest Revision")
        self.getPreviewBtn = QtGui.QPushButton("Preview Scene")
        self.getPreviewBtn.setEnabled(False)

        self.fileTreeModel = QtGui.QFileSystemModel()
        self.fileTreeModel.setRootPath(self.p4.cwd)

        self.fileTree = QtGui.QTreeView()
        self.fileTree.setModel(self.fileTreeModel)
        self.fileTree.setRootIndex(self.fileTreeModel.index(self.p4.cwd))
        self.fileTree.setColumnWidth(0, 180)

        headers = ["Revision", "User", "Action",
                   "Date", "Client", "Description"]

        self.tableWidget = QtGui.QTableWidget()
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setMaximumHeight(200)
        self.tableWidget.setMinimumWidth(500)
        self.tableWidget.setHorizontalHeaderLabels(headers)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(
            QtGui.QAbstractItemView.SingleSelection)

        self.statusBar = QtGui.QStatusBar()
        # self.statusBar.showMessage("Test")

        self.horizontalLine = QtGui.QFrame()
        self.horizontalLine.setFrameShape(QtGui.QFrame.Shape.HLine)

        if AppUtils.getCurrentSceneFile():
            self.fileTree.setCurrentIndex(
                self.fileTreeModel.index(AppUtils.getCurrentSceneFile()))
            self.loadFileLog()

    def create_layout(self):
        '''
        Create the layouts and add widgets
        '''
        check_box_layout = QtGui.QHBoxLayout()
        check_box_layout.setContentsMargins(2, 2, 2, 2)

        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)

        main_layout.addWidget(self.fileTree)
        main_layout.addWidget(self.tableWidget)

        bottomLayout = QtGui.QHBoxLayout()
        bottomLayout.addWidget(self.getRevisionBtn)
        bottomLayout.addSpacerItem(QtGui.QSpacerItem(20, 16))
        bottomLayout.addWidget(self.getPreviewBtn)
        bottomLayout.addSpacerItem(QtGui.QSpacerItem(20, 16))
        bottomLayout.addWidget(self.getLatestBtn)

        main_layout.addLayout(bottomLayout)
        main_layout.addWidget(self.horizontalLine)
        main_layout.addWidget(self.statusBar)

        self.setLayout(main_layout)

    def create_connections(self):
        '''
        Create the signal/slot connections
        '''
        self.fileTree.clicked.connect(self.loadFileLog)
        self.getLatestBtn.clicked.connect(self.onSyncLatest)
        self.getRevisionBtn.clicked.connect(self.onRevertToSelection)
        self.getPreviewBtn.clicked.connect(self.getPreview)

    #--------------------------------------------------------------------------
    # SLOTS
    #--------------------------------------------------------------------------
    def getPreview(self, *args):
        index = self.tableWidget.currentRow()
        item = self.fileRevisions[index]
        revision = item['revision']

        index = self.fileTree.selectedIndexes()[0]
        if not index:
            return

        filePath = self.fileTreeModel.fileInfo(index).absoluteFilePath()
        fileName = os.path.basename(filePath)

        path = os.path.join(tempPath, fileName)

        try:
            tmpPath = path
            self.p4.run_print(
                "-o", tmpPath, "{0}#{1}".format(filePath, revision))
            p4_logger.info(
                "Synced preview to {0} at revision {1}".format(tmpPath, revision))
            if self.isSceneFile:
                AppUtils.openScene(tmpPath)
            else:
                Utils.open_file(tmpPath)

        except P4Exception as e:
            displayErrorUI(e)

    def onRevertToSelection(self, *args):
        index = self.tableWidget.rowCount() - 1
        item = self.fileRevisions[index]
        currentRevision = item['revision']

        index = self.tableWidget.currentRow()
        item = self.fileRevisions[index]
        rollbackRevision = item['revision']

        index = self.fileTree.selectedIndexes()[0]
        if not index:
            return

        filePath = self.fileTreeModel.fileInfo(index).absoluteFilePath()

        desc = "Rollback #{0} to #{1}".format(
            currentRevision, rollbackRevision)
        if Utils.syncPreviousRevision(self.p4, filePath, rollbackRevision, desc):
            QtGui.QMessageBox.information(
                mainParent, "Success", "Successful {0}".format(desc))

        self.loadFileLog()

    def onSyncLatest(self, *args):
        index = self.fileTree.selectedIndexes()[0]
        if not index:
            return

        filePath = self.fileTreeModel.fileInfo(index).absoluteFilePath()

        try:
            self.p4.run_sync("-f", filePath)
            p4_logger.info("{0} synced to latest version".format(filePath))
            self.loadFileLog()
        except P4Exception as e:
            displayErrorUI(e)

    def loadFileLog(self, *args):
        index = self.fileTree.selectedIndexes()[0]
        if not index:
            return

        self.statusBar.showMessage("")

        self.getPreviewBtn.setEnabled(True)
        filePath = self.fileTreeModel.fileInfo(index).absoluteFilePath()

        if Utils.queryFileExtension(filePath, ['.ma', '.mb']):
            # self.getPreviewBtn.setEnabled(True)
            self.getPreviewBtn.setText("Preview Scene Revision")
            self.isSceneFile = True
        else:
            # self.getPreviewBtn.setEnabled(False)
            self.getPreviewBtn.setText("Preview File Revision")
            self.isSceneFile = False

        if os.path.isdir(filePath):
            return

        try:
            files = self.p4.run_filelog("-l", filePath)
        except P4Exception as e:
            # TODO - Better error handling here, what if we can't connect etc
            #eMsg, type = parsePerforceError(e)
            self.statusBar.showMessage(
                "{0} isn't on client".format(os.path.basename(filePath)))
            self.tableWidget.clearContents()
            self.getLatestBtn.setEnabled(False)
            self.getPreviewBtn.setEnabled(False)
            return

        self.getLatestBtn.setEnabled(True)
        self.getPreviewBtn.setEnabled(True)

        try:
            fileInfo = self.p4.run_fstat(filePath)
            print fileInfo
            if fileInfo:
                if 'otherLock' in fileInfo[0]:
                    self.statusBar.showMessage("{0} currently locked by {1}".format(
                        os.path.basename(filePath), fileInfo[0]['otherLock'][0]))
                    if fileInfo[0]['otherLock'][0].split('@')[0] != self.p4.user:
                        self.getRevisionBtn.setEnabled(False)
                elif 'otherOpen' in fileInfo[0]:
                    self.statusBar.showMessage("{0} currently opened by {1}".format(
                        os.path.basename(filePath), fileInfo[0]['otherOpen'][0]))
                    if fileInfo[0]['otherOpen'][0].split('@')[0] != self.p4.user:
                        self.getRevisionBtn.setEnabled(False)
                else:
                    self.statusBar.showMessage("{0} currently opened by {1}@{2}".format(
                        os.path.basename(filePath),  self.p4.user, self.p4.client))
                    self.getRevisionBtn.setEnabled(True)

        except P4Exception:
            self.statusBar.showMessage("{0} is not checked out".format(os.path.basename(filePath)))
            self.getRevisionBtn.setEnabled(True)

        # Generate revision dictionary
        self.fileRevisions = []

        for revision in files[0].each_revision():
            self.fileRevisions.append({"revision": revision.rev,
                                       "action": revision.action,
                                       "date": revision.time,
                                       "desc": revision.desc,
                                       "user": revision.user,
                                       "client": revision.client
                                       })

        self.tableWidget.setRowCount(len(self.fileRevisions))

        # Populate table
        for i, revision in enumerate(self.fileRevisions):
            # Saves us manually keeping track of the current column
            column = 0

            # Fill in the rest of the data
            change = "#{0}".format(revision['revision'])

            widget = QtGui.QWidget()
            layout = QtGui.QHBoxLayout()
            label = QtGui.QLabel(str(change))

            layout.addWidget(label)
            layout.setAlignment(QtCore.Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(layout)

            self.tableWidget.setCellWidget(i, column, widget)
            column += 1

            # User
            user = revision['user']

            widget = QtGui.QWidget()
            layout = QtGui.QHBoxLayout()
            label = QtGui.QLabel(str(user))
            label.setStyleSheet("QLabel { border: none } ")

            layout.addWidget(label)
            layout.setAlignment(QtCore.Qt.AlignCenter)
            layout.setContentsMargins(4, 0, 4, 0)
            widget.setLayout(layout)

            self.tableWidget.setCellWidget(i, column, widget)
            column += 1

            # Action
            pendingAction = revision['action']

            path = ""
            if(pendingAction == "edit"):
                path = os.path.join(iconPath, P4Icon.editFile)
            elif(pendingAction == "add"):
                path = os.path.join(iconPath, P4Icon.addFile)
            elif(pendingAction == "delete"):
                path = os.path.join(iconPath, P4Icon.deleteFile)

            widget = QtGui.QWidget()

            icon = QtGui.QPixmap(path)
            icon = icon.scaled(16, 16)

            iconLabel = QtGui.QLabel()
            iconLabel.setPixmap(icon)
            textLabel = QtGui.QLabel(pendingAction.capitalize())
            textLabel.setStyleSheet("QLabel { border: none } ")

            # @TODO Why not move these into a cute little function in a function

            layout = QtGui.QHBoxLayout()
            layout.addWidget(iconLabel)
            layout.addWidget(textLabel)
            layout.setAlignment(QtCore.Qt.AlignLeft)
            # layout.setContentsMargins(0,0,0,0)
            widget.setLayout(layout)

            self.tableWidget.setCellWidget(i, column, widget)
            column += 1

            # Date
            date = revision['date']

            widget = QtGui.QWidget()
            layout = QtGui.QHBoxLayout()
            label = QtGui.QLabel(str(date))
            label.setStyleSheet("QLabel { border: none } ")

            layout.addWidget(label)
            layout.setAlignment(QtCore.Qt.AlignCenter)
            layout.setContentsMargins(4, 0, 4, 0)
            widget.setLayout(layout)

            self.tableWidget.setCellWidget(i, column, widget)
            column += 1

            # Client
            client = revision['client']

            widget = QtGui.QWidget()
            layout = QtGui.QHBoxLayout()
            label = QtGui.QLabel(str(client))
            label.setStyleSheet("QLabel { border: none } ")

            layout.addWidget(label)
            layout.setAlignment(QtCore.Qt.AlignCenter)
            layout.setContentsMargins(4, 0, 4, 0)

            widget.setLayout(layout)

            self.tableWidget.setCellWidget(i, column, widget)
            column += 1

            # Description
            desc = revision['desc']

            widget = QtGui.QWidget()
            layout = QtGui.QHBoxLayout()
            text = QtGui.QLineEdit()
            text.setText(desc)
            text.setReadOnly(True)
            text.setAlignment(QtCore.Qt.AlignLeft)
            text.setStyleSheet("QLineEdit { border: none ")

            layout.addWidget(text)
            layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignLeft)
            layout.setContentsMargins(4, 0, 1, 0)
            widget.setLayout(layout)

            self.tableWidget.setCellWidget(i, column, widget)
            column += 1

        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.setColumnWidth(4, 90)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)


class PerforceUI:

    def __init__(self, p4):
        self.deleteUI = None
        self.submitUI = None
        self.perforceMenu = ""

        self.p4 = p4

        self.p4.connect()

        try:
            self.firstTimeLogin(enterUsername=self.p4.user is None,
                                enterPassword=self.p4.password is None)
        except P4Exception as e:
            # If user/pass is set but it fails anyway, try a last ditch attempt
            # to let the user input their stuff
            try:
                self.firstTimeLogin(enterUsername=True, enterPassword=True)
            except P4Exception as e:
                raise e

        # Validate workspace
        try:
            self.p4.cwd = self.p4.run_info()[0]['clientRoot']
        except P4Exception as e:
            displayErrorUI(e)
        except KeyError as e:
            print "No workspace found, creating default one"
            try:
                self.createWorkspace()
            except P4Exception as e:
                p4_logger.warning(e)

        self.p4.cwd = self.p4.fetch_client()['Root']

    def close(self):
        try:
            self.revisionUi.deleteLater()
        except Exception as e:
            print "Error cleaning up P4 revision UI : ", e

        try:
            self.openedUi.deleteLater()
        except Exception  as e:
            print "Error cleaning up P4 opened UI : ", e

        try:
            # Deleting maya menus is bad, but this is a dumb way of error checking
            if "PerforceMenu" in self.perforceMenu:
                AppUtils.closeWindow(self.perforceMenu)
            else:
                raise RuntimeError("Menu name doesn't seem to belong to Perforce, not deleting")
        except Exception  as e:
            print "Error cleaning up P4 menu : ", e

        try:
            self.submitUI.deleteLater()
        except Exception  as e:
            print "Error cleaning up P4 submit UI : ", e

        p4_logger.info("Disconnecting from server")
        try:
            self.p4.disconnect()
        except Exception  as e:
            print "Error disconnecting P4 daemon : ", e

    def addMenu(self):
        # try:
        #     AppUtils.closeWindow(self.perforceMenu)
        # except:
        #     pass

        import maya.mel
        # import maya.utils as mu
        import maya.cmds as cmds
        # import maya.OpenMayaUI as omui
        # from shiboken import wrapInstance

        gMainWindow = maya.mel.eval('$temp1=$gMainWindow')
        self.perforceMenu = cmds.menu("PerforceMenu", parent=gMainWindow, tearOff=True, label='Perforce')

        # %TODO Move these to MayaUtils
        # %TODO Hard coded icons are bad?

        cmds.setParent(self.perforceMenu, menu=True)
        cmds.menuItem(label="Client Commands", divider=True)
        cmds.menuItem(label="Checkout File(s)",                     image=os.path.join(
            iconPath, "File0078.png"), command=self.checkoutFile)
        cmds.menuItem(label="Checkout Folder",                     image=os.path.join(
            iconPath, "File0186.png"), command=self.checkoutFolder)
        cmds.menuItem(label="Mark for Delete",                      image=os.path.join(
            iconPath, "File0253.png"), command=self.deleteFile)
        cmds.menuItem(label="Show Changelist",                      image=os.path.join(
            iconPath, "File0252.png"), command=self.queryOpened)

        # cmds.menuItem(divider=True)
        # self.lockFile = cmds.menuItem(label="Lock This File",       image = os.path.join(iconPath, "File0143.png"), command = self.lockThisFile                 )
        # self.unlockFile = cmds.menuItem(label="Unlock This File",   image = os.path.join(iconPath, "File0252.png"), command = self.unlockThisFile, en=False     )
        # cmds.menuItem(label = "Locking", divider=True)
        # cmds.menuItem(label="Lock File",                            image = os.path.join(iconPath, "File0143.png"), command = self.lockFile                 )
        # cmds.menuItem(label="Unlock File",                          image = os.path.join(iconPath, "File0252.png"), command = self.unlockFile               )

        cmds.menuItem(label="Depot Commands", divider=True)
        cmds.menuItem(label="Submit Change",                        image=os.path.join(
            iconPath, "File0107.png"), command=self.submitChange)
        cmds.menuItem(label="Sync All",                             image=os.path.join(iconPath, "File0175.png"), command=self.syncAllChanged)
        cmds.menuItem(label="Sync All - Force",                     image=os.path.join(iconPath, "File0175.png"), command=self.syncAll)
        cmds.menuItem(label="Sync All References",                  image=os.path.join(iconPath, "File0320.png"), command=self.syncAllChanged, en=False)
        #cmds.menuItem(label="Get Latest Scene",                    image = os.path.join(iconPath, "File0275.png"), command = self.syncFile                 )
        cmds.menuItem(label="Show Depot History",                   image=os.path.join(
            iconPath, "File0279.png"), command=self.fileRevisions)

        cmds.menuItem(label="Scene", divider=True)
        cmds.menuItem(label="File Status",                          image=os.path.join(
            iconPath, "File0409.png"), command=self.querySceneStatus)

        cmds.menuItem(label="Utility", divider=True)
        cmds.menuItem(label="Create Asset",                          image=os.path.join(
            iconPath, "File0352.png"), command=self.createAsset)
        cmds.menuItem(label="Create Shot",                          image=os.path.join(
            iconPath, "File0104.png"), command=self.createShot)

        cmds.menuItem(divider=True)
        cmds.menuItem(subMenu=True, tearOff=False, label="Miscellaneous",
                      image=os.path.join(iconPath, "File0411.png"))
        cmds.menuItem(label="Server", divider=True)
        cmds.menuItem(label="Login as user",                            image=os.path.join(
            iconPath, "File0077.png"), command=self.loginAsUser)
        #cmds.menuItem(label="Change Password",                     image = os.path.join(iconPath, "File0143.png"), command = "print('Change password')",   en=False    )
        cmds.menuItem(label="Server Info",                               image=os.path.join(
            iconPath, "File0031.png"),  command=self.queryServerStatus)
        cmds.menuItem(label="Workspace", divider=True)
        cmds.menuItem(label="Create Workspace",                      image=os.path.join(
            iconPath, "File0238.png"), command=self.createWorkspace)
        cmds.menuItem(label="Set Current Workspace",                      image=os.path.join(
            iconPath, "File0044.png"), command=self.setCurrentWorkspace)
        cmds.menuItem(label="Debug", divider=True)
        cmds.menuItem(label="Delete all pending changes",                      image=os.path.join(
            iconPath, "File0280.png"), command=self.deletePending)
        cmds.setParent( '..', menu=True )
        cmds.menuItem(label="Version {0}".format(version), en=False)

    def changePasswd(self, *args):
        return NotImplementedError("Use p4 passwd")

    def createShot(self, *args):
        shotNameDialog = QtGui.QInputDialog
        shotName = shotNameDialog.getText(
            mainParent, "Create Shot", "Shot Name:")

        if not shotName[1]:
            return

        if not shotName[0]:
            p4_logger.warning("Empty shot name")
            return

        shotNumDialog = QtGui.QInputDialog
        shotNum = shotNumDialog.getText(
            mainParent, "Create Shot", "Shot Number:")

        if not shotNum[1]:
            return

        if not shotNum[0]:
            p4_logger.warning("Empty shot number")
            return

        shotNumberInt = -1
        try:
            shotNumberInt = int(shotNum[0])
        except ValueError as e:
            p4_logger.warning(e)
            return

        p4_logger.info("Creating folder structure for shot {0}/{1} in {2}".format(
            shotName[0], shotNumberInt, self.p4.cwd))
        dir = Utils.createShotFolders(self.p4.cwd, shotName[0], shotNumberInt)
        self.run_checkoutFolder(None, dir)

    def createAsset(self, *args):
        assetNameDialog = QtGui.QInputDialog
        assetName = assetNameDialog.getText(
            mainParent, "Create Asset", "Asset Name:")

        if not assetName[1]:
            return

        if not assetName[0]:
            p4_logger.warning("Empty asset name")
            return

        p4_logger.info("Creating folder structure for asset {0} in {1}".format(
            assetName[0], self.p4.cwd))
        dir = Utils.createAssetFolders(self.p4.cwd, assetName[0])
        self.run_checkoutFolder(None, dir)

    def loginAsUser(self, *args):
        self.firstTimeLogin(enterUsername=True, enterPassword=True)

    def firstTimeLogin(self, enterUsername=True, enterPassword=True, *args):
        username = None
        password = None

        if enterUsername:
            usernameInputDialog = QtGui.QInputDialog
            username = usernameInputDialog.getText(
                mainParent, "Enter username", "Username:")

            if not username[1]:
                raise ValueError("Invalid username")

            self.p4.user = str(username[0])

        if enterPassword:
            passwordInputDialog = QtGui.QInputDialog
            password = passwordInputDialog.getText(
                mainParent, "Enter password", "Password:")

            if not password[1]:
                raise ValueError("Invalid password")

            self.p4.password = str(password[0])

        # Validate SSH Login / Attempt to login
        try:
            p4_logger.info(self.p4.run_login("-a"))
        except P4Exception as e:
            regexKey = re.compile(ur'(?:[0-9a-fA-F]:?){40}')
            # regexIP = re.compile(ur'[0-9]+(?:\.[0-9]+){3}?:[0-9]{4}')
            errorMsg = str(e).replace('\\n', ' ')

            key = re.findall(regexKey, errorMsg)
            # ip = re.findall(regexIP, errorMsg)

            if key:
                p4_logger.info(self.p4.run_trust("-i", key[0]))
                p4_logger.info(self.p4.run_login("-a"))
            else:
                raise e

        if username:
            Utils.writeToP4Config(self.p4.p4config_file,
                                  "P4USER", str(username[0]))
            
        # if password:
        #     Utils.writeToP4Config(self.p4.p4config_file,
        #                           "P4PASSWD", str(password[0]))

    def setCurrentWorkspace(self, *args):
        workspacePath = QtGui.QFileDialog.getExistingDirectory(
            mainParent, "Select existing workspace")

        for client in self.p4.run_clients():
            if workspacePath.replace("\\","/") == client['Root'].replace("\\","/"):
                root, client = os.path.split(str(workspacePath))
                self.p4.client = client

                p4_logger.info("Setting current client to {0}".format(client))
                # REALLY make sure we save the P4CLIENT variable
                if platform.system() == "Linux" or platform.system() == "Darwin":
                    os.environ['P4CLIENT'] = self.p4.client
                    Utils.saveEnvironmentVariable("P4CLIENT", self.p4.client)
                else:
                    self.p4.set_env('P4CLIENT', self.p4.client)

                Utils.writeToP4Config(
                    self.p4.p4config_file, "P4CLIENT", self.p4.client)
                break
        else:
            QtGui.QMessageBox.warning(
                mainParent, "Perforce Error", "{0} is not a workspace root".format(workspacePath))

    def createWorkspace(self, *args):
        workspaceRoot = None

        i = 0
        while i < 3:
            workspaceRoot = QtGui.QFileDialog.getExistingDirectory(
                AppUtils.main_parent_window(), "Specify workspace root folder")
            i += 1
            if workspaceRoot:
                break
        else:
            raise IOError("Can't set workspace")

        try:
            workspaceSuffixDialog = QtGui.QInputDialog
            workspaceSuffix = workspaceSuffixDialog.getText(
                mainParent, "Workspace", "Optional Name Suffix (e.g. Uni, Home):")

            Utils.createWorkspace(self.p4, workspaceRoot,
                                  str(workspaceSuffix[0]))
            Utils.writeToP4Config(self.p4.p4config_file,
                                  "P4CLIENT", self.p4.client)
        except P4Exception as e:
            displayErrorUI(e)

    # Open up a sandboxed QFileDialog and run a command on all the selected
    # files (and log the output)
    def __processClientFile(self, title, finishCallback, preCallback, p4command, *p4args):
        fileDialog = QtGui.QFileDialog(mainParent, title, str(self.p4.cwd))

        def onEnter(*args):
            if not Utils.isPathInClientRoot(self.p4, args[0]):
                fileDialog.setDirectory(self.p4.cwd)

        def onComplete(*args):
            selectedFiles = []
            error = None

            if preCallback:
                preCallback(fileDialog.selectedFiles())

            # Only add files if we didn't cancel
            if args[0] == 1:
                for file in fileDialog.selectedFiles():
                    if Utils.isPathInClientRoot(self.p4, file):
                        try:
                            p4_logger.info(p4command(p4args, file))
                            selectedFiles.append(file)
                        except P4Exception as e:
                            p4_logger.warning(e)
                            error = e
                    else:
                        p4_logger.warning(
                            "{0} is not in client root.".format(file))

            fileDialog.deleteLater()
            if finishCallback:
                finishCallback(selectedFiles, error)

        fileDialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
        fileDialog.directoryEntered.connect(onEnter)
        fileDialog.finished.connect(onComplete)
        fileDialog.show()

    # Open up a sandboxed QFileDialog and run a command on all the selected folders (and log the output)
    # %TODO This should be refactored
    def __processClientDirectory(self, title, finishCallback, preCallback, p4command, *p4args):
        fileDialog = QtGui.QFileDialog(mainParent, title, str(self.p4.cwd))

        def onEnter(*args):
            if not Utils.isPathInClientRoot(self.p4, args[0]):
                fileDialog.setDirectory(self.p4.cwd)

        def onComplete(*args):
            selectedFiles = []
            error = None

            if preCallback:
                preCallback(fileDialog.selectedFiles())

            # Only add files if we didn't cancel
            if args[0] == 1:
                for file in fileDialog.selectedFiles():
                    if Utils.isPathInClientRoot(self.p4, file):
                        try:
                            p4_logger.info(p4command(p4args, file))
                            selectedFiles.append(file)
                        except P4Exception as e:
                            p4_logger.warning(e)
                            error = e
                    else:
                        p4_logger.warning(
                            "{0} is not in client root.".format(file))

            fileDialog.deleteLater()
            if finishCallback:
                finishCallback(selectedFiles, error)

        fileDialog.setFileMode(QtGui.QFileDialog.DirectoryOnly)
        fileDialog.directoryEntered.connect(onEnter)
        fileDialog.finished.connect(onComplete)
        fileDialog.show()

    def checkoutFile(self, *args):
        def openFirstFile(selected, error):
            if not error:
                if len(selected) == 1 and Utils.queryFileExtension(selected[0], sceneFiles):
                    if not AppUtils.getCurrentSceneFile() == selected[0]:
                        result = QtGui.QMessageBox.question(
                            mainParent, "Open Scene?", "Do you want to open the checked out scene?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                        if result == QtGui.QMessageBox.StandardButton.Yes:
                            AppUtils.openScene(selected[0])

        self.__processClientFile(
            "Checkout file(s)", openFirstFile, None, self.run_checkoutFile)

    def checkoutFolder(self, *args):
        self.__processClientDirectory(
            "Checkout file(s)", None, None, self.run_checkoutFolder)

    def run_checkoutFolder(self, *args):
        allFiles = []
        for folder in args[1:]:
            allFiles += Utils.queryFilesInDirectory(folder)

        self.run_checkoutFile(None, *allFiles)

    def deletePending(self, *args):
        changes = Utils.queryChangelists(self.p4, "pending")
        Utils.forceChangelistDelete(self.p4, changes)

    def run_checkoutFile(self, *args):
        for file in args[1:]:
            p4_logger.info("Processing {0}...".format(file))
            result = None
            try:
                result = self.p4.run_fstat(file)
            except P4Exception as e:
                pass

            try:
                if result:
                    if 'otherLock' in result[0]:
                        raise P4Exception("[Warning]: {0} already locked by {1}\"".format(
                            file, result[0]['otherLock'][0]))
                    else:
                        p4_logger.info(self.p4.run_edit(file))
                        p4_logger.info(self.p4.run_lock(file))
                else:
                    p4_logger.info(self.p4.run_add(file))
                    p4_logger.info(self.p4.run_lock(file))
            except P4Exception as e:
                displayErrorUI(e)

    def deleteFile(self, *args):
        def makeFilesReadOnly(files):
            Utils.addReadOnlyBit(files)

        self.__processClientFile(
            "Delete file(s)", None, makeFilesReadOnly, self.p4.run_delete)

    def revertFile(self, *args):
        self.__processClientFile(
            "Revert file(s)", None, None, self.p4.run_revert, "-k")

    def lockFile(self, *args):
        self.__processClientFile("Lock file(s)", None, None, self.p4.run_lock)

    def unlockFile(self, *args):
        self.__processClientFile(
            "Unlock file(s)", None, None, self.p4.run_unlock)

    def lockThisFile(self, *args):
        raise NotImplementedError(
            "Scene lock not implemented (use regular lock)")

        # file = AppUtils.getCurrentSceneFile()

        # if not file:
        #     p4_logger.warning("Current scene has no name")
        #     return

        # if not Utils.isPathInClientRoot(self.p4, file):
        #     p4_logger.warning("{0} is not in client root".format(file))
        #     return

        # try:
        #     self.p4.run_lock(file)
        #     p4_logger.info("Locked file {0}".format(file))

        #     #@todo Move these into MayaUtils.py
        #     # cmds.menuItem(self.unlockFile, edit=True, en=True)
        #     # cmds.menuItem(self.lockFile, edit=True, en=False)
        # except P4Exception as e:
        #     displayErrorUI(e)

    def unlockThisFile(self, *args):
        raise NotImplementedError(
            "Scene unlock not implemented (use regular unlock)")

        # file = AppUtils.getCurrentSceneFile()

        # if not file:
        #     p4_logger.warning("Current scene has no name")
        #     return

        # if not Utils.isPathInClientRoot(self.p4, file):
        #     p4_logger.warning("{0} is not in client root".format(file))
        #     return

        # try:
        #     self.p4.run_unlock( file )
        #     p4_logger.info("Unlocked file {0}".format(file))

        #     # cmds.menuItem(self.unlockFile, edit=True, en=False)
        #     # cmds.menuItem(self.lockFile, edit=True, en=True)
        # except P4Exception as e:
        #     displayErrorUI(e)

    # def syncFile(self, *args):
    #     self.__processClientFile("Sync file(s)", self.p4.run_sync)

    def querySceneStatus(self, *args):
        try:
            scene = AppUtils.getCurrentSceneFile()
            if not scene:
                p4_logger.warning("Current scene file isn't saved.")
                return

            result = self.p4.run_fstat("-Oa", scene)[0]
            text = ""
            for x in result:
                text += ("{0} : {1}\n".format(x, result[x]))
            QtGui.QMessageBox.information(mainParent, "Scene Info", text)
        except P4Exception as e:
            displayErrorUI(e)

    def queryServerStatus(self, *args):
        try:
            result = self.p4.run_info()[0]
            text = ""
            for x in result:
                text += ("{0} : {1}\n".format(x, result[x]))
            QtGui.QMessageBox.information(mainParent, "Server Info", text)
        except P4Exception as e:
            displayErrorUI(e)

    def fileRevisions(self, *args):
        try:
            self.revisionUi.deleteLater()
        except:
            pass

        self.revisionUi = FileRevisionUI()

        # Delete the UI if errors occur to avoid causing winEvent and event
        # errors (in Maya 2014)
        try:
            self.revisionUi.create(self.p4)
            self.revisionUi.show()
        except:
            self.revisionUi.deleteLater()
            traceback.print_exc()

    def queryOpened(self, *args):
        try:
            self.openedUi.deleteLater()
        except:
            pass

        self.openedUi = OpenedFilesUI()

        # Delete the UI if errors occur to avoid causing winEvent and event
        # errors (in Maya 2014)
        try:
            self.openedUi.create(self.p4)
            self.openedUi.show()
        except:
            self.openedUi.deleteLater()
            traceback.print_exc()

    def submitChange(self, *args):
        try:
            self.submitUI.deleteLater()
        except:
            pass

        self.submitUI = SubmitChangeUi()

        # Delete the UI if errors occur to avoid causing winEvent
        # and event errors (in Maya 2014)
        try:
            files = self.p4.run_opened(
                "-u", self.p4.user, "-C", self.p4.client, "...")

            AppUtils.refresh()

            entries = []
            for file in files:
                filePath = file['clientFile']

                entry = {'File': filePath,
                         'Folder': os.path.split(filePath)[0],
                         'Type': file['type'],
                         'Pending_Action': file['action'],
                         }

                entries.append(entry)

            print "Submit Files : ", files

            self.submitUI.create(self.p4, entries)
            self.submitUI.show()
        except:
            self.submitUI.deleteLater()
            traceback.print_exc()

    def syncFile(self, *args):
        try:
            self.p4.run_sync("-f", AppUtils.getCurrentSceneFile())
            p4_logger.info("Got latest revision for {0}".format(
                AppUtils.getCurrentSceneFile()))
        except P4Exception as e:
            displayErrorUI(e)

    def syncAll(self, *args):
        try:
            self.p4.run_sync("-f", "...")
            p4_logger.info("Got latest revisions for client")
        except P4Exception as e:
            displayErrorUI(e)

    def syncAllChanged(self, *args):
        try:
            self.p4.run_sync("...")
            p4_logger.info("Got latest revisions for client")
        except P4Exception as e:
            displayErrorUI(e)

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
    print p4.client
    print p4.port

    Callbacks.initCallbacks()

    try:
        ui = PerforceUI(p4)

        ui.addMenu()
    except ValueError as e:
        p4_logger.critical(e)

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


# %Todo Implement this >>

# import sys, os
# from PySide import QtCore, QtGui

# from P4 import P4, P4Exception

# import sys

# #http://stackoverflow.com/questions/32229314/pyqt-how-can-i-set-row-heights-of-qtreeview

# class TreeItem(object):
#     def __init__(self, data, parent=None):
#         self.parentItem = parent
#         self.data = data
#         self.childItems = []

#     def appendChild(self, item):
#         self.childItems.append(item)

#     def popChild(self):
#         if self.childItems:
#             self.childItems.pop()

#     def row(self):
#         if self.parentItem:
#             return self.parentItem.childItems.index(self)
#         return 0

# def reconnect():
#     p4.disconnect()
#     p4.connect()
#     p4.password = "contact_dev"
#     p4.run_login()

# def epochToTimeStr(time):
#     import datetime
# return datetime.datetime.utcfromtimestamp( int(time)
# ).strftime("%d/%m/%Y %H:%M:%S")

# def perforceListDir(p4path):
#     result = []

#     if p4path[-1] == '/' or p4path[-1] == '\\':
#         p4path = p4path[:-1]

#     path = "{0}/{1}".format(p4path, '*')

#     isDepotPath = p4path.startswith("//depot")

#     dirs = []
#     files = []

#     # Dir silently does nothing if there are no dirs
#     try:
#         dirs = p4.run_dirs( path )
#     except P4Exception as e:
#         pass

#     # Files will return an exception if there are no files in the dir
#     # Stupid inconsistency imo
#     try:
#         if isDepotPath:
#             files = p4.run_files( path )
#         else:
#             tmp = p4.run_have( path )
#             for fileItem in tmp:
#                 files += p4.run_fstat( fileItem['clientFile'] )
#     except P4Exception as e:
#         pass

#     result = []

#     for dir in dirs:
#         if isDepotPath:
#             dirName = dir['dir'][8:]
#         else:
#             dirName = dir['dir']

#         tmp = { 'name' : os.path.basename(dirName),
#                 'path' : dir['dir'],
#                 'time' : '',
#                 'type' : 'Folder',
#                 'change': ''
#                 }
#         result.append(tmp)

#     for fileItem in files:
#         if isDepotPath:
#             deleteTest = p4.run("filelog", "-t", fileItem['depotFile'] )[0]
#             isDeleted = deleteTest['action'][0] == "delete"
#             fileType = fileItem['type']
#             if isDeleted:
#                 fileType = "{0} [Deleted]".format(fileType)
#             # Remove //depot/ from the path for the 'pretty' name
#             tmp = { 'name' : os.path.basename( fileItem['depotFile'][8:] ),
#                     'path' : fileItem['depotFile'],
#                     'time' : epochToTimeStr( fileItem['time'] ) ,
#                     'type' : fileType,
#                     'change': fileItem['change']
#                     }
#             result.append(tmp)
#         else:
#             deleteTest = p4.run("filelog", "-t", fileItem['clientFile'] )[0]
#             isDeleted = deleteTest['action'][0] == "delete"
#             fileType = fileItem['headType']
#             if isDeleted:
#                 fileType = "{0} [Deleted]".format(fileType)
#             tmp = { 'name' : os.path.basename( fileItem['clientFile'] ),
#                     'path' : fileItem['clientFile'],
#                     'time' : epochToTimeStr( fileItem['headModTime'] ) ,
#                     'type' : fileType,
#                     'change': fileItem['headChange']
#                     }
#             result.append(tmp)

#     return sorted(result, key=lambda k: k['name'] )


# def perforceIsDir(p4path):
#     try:
#         if p4path[-1] == '/' or p4path[-1] == '\\':
#             p4path = p4path[:-1]
#         result = p4.run_dirs(p4path)
#         return len(result) > 0
#     except P4Exception as e:
#         print e
#         return False


# def p4Filelist(dir, findDeleted = False):
#     p4path = '/'.join( [dir, '*'] )
#     try:
#         files = p4.run_filelog("-t", p4path)
#     except P4Exception as e:
#         print e
#         return []

#     results = []

#     for x in files:
#         latestRevision = x.revisions[0]
#         print latestRevision.action, latestRevision.depotFile

#         if not findDeleted and latestRevision.action == 'delete':
#             continue
#         else:
#             results.append( { 'name' : latestRevision.depotFile,
#                             'action' : latestRevision.action,
#                             'change' : latestRevision.change,
#                             'time': latestRevision.time,
#                             'type' : latestRevision.type
#                             }
#                           )

#     filesInCurrentChange = p4.run_opened(p4path)
#     for x in filesInCurrentChange:
#         print x
#         results.append( { 'name' : x['clientFile'],
#                           'action' : x['action'],
#                           'change' : x['change'],
#                           'time' : "",
#                           'type' : x['type']
#                         }
#                        )

#     return results

# class TreeModel(QtCore.QAbstractItemModel):
#     def __init__(self, parent=None):
#         super(TreeModel, self).__init__(parent)

#         self.rootItem = TreeItem(None)
#         self.showDeleted = False

#     def populate(self, rootdir = "//depot", findDeleted=False):
#         self.rootItem = TreeItem(None)
#         self.showDeleted = findDeleted

#         depotPath = False
#         if "depot" in rootdir:
#             depotPath = True

#         p4path = '/'.join( [rootdir, '*'] )

#         if depotPath:
#             dirs = p4.run_dirs( p4path )
#         else:
#             dirs = p4.run_dirs('-H', p4path )


#         for dir in dirs:
#             dirName = os.path.basename(dir['dir'])
#             #subDir = '/'.join( [rootdir, dirName )] )
#             data = [dirName , "Folder", "", "", ""]

#             treeItem = TreeItem(data, self.rootItem)
#             self.rootItem.appendChild(treeItem)

#             treeItem.appendChild(None)

#             files = p4Filelist(dir['dir'], findDeleted)

#             for f in files:
#                 fileName = os.path.basename( f['name'] )
#                 data = [fileName, f['type'], f['time'], f['action'], f['change']]

#                 fileItem = TreeItem(data, treeItem)
#                 treeItem.appendChild(fileItem)


#     # def populate(self, rootdir):
#     #     rootdir = rootdir.replace('\\', '/')

#     #     print "Scanning subfolders in {0}...".format(rootdir)

#         # import maya.cmds as cmds
#         # cmds.refresh()

#         # def scanDirectoryPerforce(root, treeItem):
#         #     change = p4.run_opened()

#         #     for item in perforceListDir(root):
#         #         itemPath = "{0}/{1}".format(root, item['name'] ) # os.path.join(root, item)
#         #         #print "{0}{1}{2}".format( "".join(["\t" for i in range(depth)]), '+' if perforceIsDir(itemPath) else '-', item['name'] )

#         #         data = [ item['name'], item['type'], item['time'], item['change'] ]

#         #         childDir = TreeItem( data, treeItem)
#         #         treeItem.appendChild( childDir )

#         #         tmpDir = TreeItem( [ "TMP", "", "", "" ], childDir )
#         #         childDir.appendChild( None )

#         #         #print itemPath, perforceIsDir( itemPath )
#         #         #if perforceIsDir( itemPath ):
#         #         #    scanDirectoryPerforce(itemPath, childDir)

#         # def scanDirectory(root, treeItem):
#         #     for item in os.listdir(root):
#         #         itemPath = os.path.join(root, item)
#         #         print "{0}{1}{2}".format( "".join(["\t" for i in range(depth)]), '+' if os.path.isdir(itemPath) else '-', item)
#         #         childDir = TreeItem( [item], treeItem)
#         #         treeItem.appendChild( childDir )
#         #         if os.path.isdir( itemPath ):
#         #             scanDirectory(itemPath, childDir)

#         # scanDirectoryPerforce(rootdir, self.rootItem )

#         #print dirName
#         #directory = "{0}:{1}".format(i, os.path.basename(dirName))
#         #childDir = TreeItem( [directory], self.rootItem)
#         #self.rootItem.appendChild( childDir )

#         #for fname in fileList:
#         #    childFile = TreeItem(fname, childDir)
#         #    childDir.appendChild([childFile])

#         #        for i,c  in enumerate("abcdefg"):
#         #           child = TreeItem([i],self.rootItem)
#         #           self.rootItem.appendChild(child)

#     def columnCount(self, parent):
#         return 5

#     def data(self, index, role):
#         column = index.column()
#         if not index.isValid():
#             return None
#         if role == QtCore.Qt.DisplayRole:
#             item = index.internalPointer()
#             return item.data[column]
#         elif role == QtCore.Qt.SizeHintRole:
#             return QtCore.QSize(20, 20)
#         elif role == QtCore.Qt.DecorationRole:
#             if column == 1:
#                 itemType = index.internalPointer().data[column]
#                 isDeleted = index.internalPointer().data[3] == 'delete'

#                 if isDeleted:
# return QtGui.QIcon(
# r"/home/i7245143/src/MayaPerforce/Perforce/images/File0104.png" )

#                 if itemType == "Folder":
#                     return QtGui.QIcon( r"/home/i7245143/src/MayaPerforce/Perforce/images/File0059.png" )
#                 elif "binary" in itemType:
#                     return QtGui.QIcon( r"/home/i7245143/src/MayaPerforce/Perforce/images/File0315.png" )
#                 elif "text" in itemType:
#                     return QtGui.QIcon( r"/home/i7245143/src/MayaPerforce/Perforce/images/File0027.png" )
#                 else:
# return QtGui.QIcon(
# r"/home/i7245143/src/MayaPerforce/Perforce/images/File0106.png" )

#                 #icon = QtGui.QFileIconProvider(QtGui.QFileIconProvider.Folder)

#                 return icon
#             else:
#                 return None

#         return None


#     def flags(self, index):
#         if not index.isValid():
#             return QtCore.Qt.NoItemFlags
#         return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

#     def headerData(self, section, orientation, role):
#         if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
#             return ["Filename", "Type", "Modification Time", "Action", "Change"][section]
#         return None

#     def index(self, row, column, parent):
#         if not self.hasIndex(row, column, parent):
#             return QtCore.QModelIndex()

#         if not parent.isValid():
#             parentItem = self.rootItem
#         else:
#             parentItem = parent.internalPointer()

#         childItem = parentItem.childItems[row]
#         if childItem:
#             return self.createIndex(row, column, childItem)
#         else:
#             return QtCore.QModelIndex()

#     def parent(self, index):
#         if not index.isValid():
#             return QtCore.QModelIndex()
#         parentItem = index.internalPointer().parentItem
#         if parentItem == self.rootItem:
#             return QtCore.QModelIndex()
#         return self.createIndex(parentItem.row(), 0, parentItem)

#     def rootrowcount(self):
#         return len(self.rootItem.childItems)

#     def rowCount(self, parent):
#         if parent.column() > 0:
#             return 0
#         if not parent.isValid():
#             parentItem = self.rootItem
#         else:
#             parentItem = parent.internalPointer()
#         return len(parentItem.childItems)


# # allFiles = p4.run_files("//depot/...")
# # hiddenFiles = p4.run_files("//depot/.../.*")

# # testData = [['assets', '.place-holder'], ['assets', 'heroTV', 'lookDev', 'heroTV_lookDev.ma'], ['assets', 'heroTV', 'lookDev', 'heroTv_lookdev.ma'], ['assets', 'heroTV', 'modelling', '.place-holder'], ['assets', 'heroTV', 'modelling', 'Old_TV.obj'], ['assets', 'heroTV', 'modelling', 'heroTv_wip.ma'], ['assets', 'heroTV', 'rigging', '.place-holder'], ['assets', 'heroTV', 'texturing', '.place-holder'], ['assets', 'heroTV', 'workspace.mel'], ['assets', 'lookDevSourceimages', 'Garage.EXR'], ['assets', 'lookDevSourceimages', 'UVtile.jpg'], ['assets', 'lookDevSourceimages', 'macbeth_background.jpg'], ['assets', 'lookDevTemplate.ma'], ['assets', 'previs_WIP.ma'], ['assets', 'previs_slapcomp_WIP.ma'], ['audio', '.place-holder'], ['finalEdit', 'delivery', '.place-holder'], ['finalEdit', 'projects', '.place-holder'], ['finalEdit', 'test'], ['finalEdit', 'test.ma'], ['shots', '.place-holder'], ['shots', 'space', 'space_sh_010', 'cg', 'maya', 'scenes', 'spc_sh_010_animBuild_WIP.ma']]

# # result = {}

# # files = [ item['depotFile'][8:].split('/') for item in allFiles ]

# # for item in files:
# #     print item

# # from collections import defaultdict
# # deepestIndex, deepestPath = max(enumerate(files), key = lambda tup: len(tup[1]))


# try:
#     print p4
# except:
#     p4 = P4()
#     p4.user = "tminor"
#     p4.password = "contact_dev"
#     p4.port = "ssl:52.17.163.3:1666"
#     p4.connect()
#     p4.run_login()

# reconnect()

# # Iterate upwards until we have the full path to the node
# def fullPath(idx):
#     result = [ idx ]

#     parent = idx.parent()
#     while True:
#         if not parent.isValid():
#             break
#         result.append( parent )
#         parent = parent.parent()

#     return list(reversed(result))


# def populateSubDir(idx, root = "//depot", findDeleted=False):
#     idxPathModel = fullPath(idx)
#     idxPathSubDirs = [ idxPath.data() for idxPath in idxPathModel ]
#     idxFullPath = os.path.join(*idxPathSubDirs)

#     if not idxFullPath:
#         idxFullPath = "."

#     children = []

#     p4path = '/'.join( [root, idxFullPath, '*'] )

#     depotPath = False
#     if "depot" in root:
#         depotPath = True

#     if depotPath:
#         p4subdirs = p4.run_dirs( p4path )
#     else:
#         p4subdirs = p4.run_dirs('-H', p4path )

#     p4subdir_names = [ child['dir'] for child in p4subdirs ]

#     treeItem = idx.internalPointer()

#     #print idx.child(0,0).data(), p4subidrs

#     if not idx.child(0,0).data() and p4subdirs:
#         # Pop empty "None" child
#         treeItem.popChild()

#         for p4child in p4subdir_names:
#             print p4child
#             data = [ os.path.basename(p4child), "Folder", "", "", "" ]

#             childData = TreeItem( data, treeItem )
#             treeItem.appendChild(childData)

#             childData.appendChild(None)

#             files = p4Filelist(p4child, findDeleted)

#             for f in files:
#                 fileName = os.path.basename( f['name'] )
#                 data = [fileName, f['type'], f['time'], f['action'], f['change']]

#                 fileData = TreeItem(data, childData)
#                 childData.appendChild(fileData)


# def tmp(*args):
#     idx = args[0]

#     children = []

#     i = 1
#     while True:
#         child = idx.child(i, 0)
#         print i, child.data()
#         if not child.isValid():
#             break

#         children.append(child)
#         i += 1

#         populateSubDir(child, findDeleted=False)

#     return

#     treeItem = idx.internalPointer()

#     idxPathModel = fullPath(idx, model.showDeleted)

#     idxPathSubDirs = [ idxPath.data() for idxPath in idxPathModel ]
#     idxFullPath = os.path.join(*idxPathSubDirs)
#     pathDepth = len(idxPathSubDirs)

#     children = []

#     p4path = "//{0}/{1}/*".format(p4.client, idxFullPath)
#     print p4path
#     p4children = p4.run_dirs("-H", p4path )
#     p4children_names = [ child['dir'] for child in p4children ]

#     if idx.child(0,0).data() == "TMP":
#         for p4child in p4children_names:
#             data = [ p4child, "", "", "" ]
#             childData = TreeItem( data, idx )
#             treeItem.appendChild(childData)

#     i = 0
#     while True:
#         child = idx.child(i, 0)
#         if not child.isValid():
#             break

#         children.append(child)
#         i += 1


#     for child in children:
#         childIdx = child.internalPointer()

#         data = [ "TEST", "TEST", "TEST", "TEST" ]
#         childDir = TreeItem( data, childIdx )
#         childIdx.appendChild( childDir )

#         tmpDir = TreeItem( [ "TMP", "", "", "", "" ], childDir )
#         childDir.appendChild( tmpDir )

#     #view.setModel(model)

# view = QtGui.QTreeView()
# view.expandAll()
# view.setWindowTitle("Perforce Depot Files")
# view.resize(512,512)
# view.expanded.connect(tmp)

# model = TreeModel()
# #model.populate("//{0}".format(p4.client), findDeleted=True)
# model.populate("//depot", findDeleted=True)

# view.setModel(model)

# #populateSubDir( view.rootIndex() )

# for i in range(model.rootrowcount()):
#     idx = model.index(i, 0, model.parent(QtCore.QModelIndex()) )

#     treeItem = idx.internalPointer()

#     populateSubDir(idx)

# #     #test = TreeItem( ["TEST", "", "", ""], treeItem  )
# #     #treeItem.appendChild( test )

# view.setColumnWidth(0, 220)
# view.setColumnWidth(1, 100)
# view.setColumnWidth(2, 120)
# view.setColumnWidth(3, 60)

# view.show()
