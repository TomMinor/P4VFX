import os

from P4 import P4, P4Exception
from qtpy import QtCore, QtGui, QtWidgets

from perforce import Utils
from perforce.PerforceUtils import CmdsChangelist
from perforce.AppInterop import interop
from perforce.PerforceUtils.TestOutputAndProgress import TestOutputAndProgress
from SubmitProgressWindow import SubmitProgressUI

class SubmitChangeUi(QtWidgets.QDialog):

    def __init__(self, parent=interop.main_parent_window()):
        super(SubmitChangeUi, self).__init__(parent)

    def create(self, p4, files=[]):
        self.p4 = p4

        path = interop.getIconPath() + "p4.png"
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
        self.submitBtn = QtWidgets.QPushButton("Submit")
        self.descriptionWidget = QtWidgets.QPlainTextEdit("<Enter Description>")
        self.descriptionLabel = QtWidgets.QLabel("Change Description:")
        self.chkboxLockedWidget = QtWidgets.QCheckBox("Keep files checked out?")

        headers = [" ", "File", "Type", "Action", "Folder"]

        self.tableWidget = QtWidgets.QTableWidget(len(self.fileList), len(headers))
        self.tableWidget.setMaximumHeight(200)
        self.tableWidget.setMinimumWidth(500)
        self.tableWidget.setHorizontalHeaderLabels(headers)

        for i, file in enumerate(self.fileList):
            # Saves us manually keeping track of the current column
            column = 0

            # Create checkbox in first column
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout()
            chkbox = QtWidgets.QCheckBox()
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
            newItem = QtWidgets.QTableWidgetItem(os.path.basename(fileName))
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

            # Text
            fileType = file['Type']
            newItem = QtWidgets.QTableWidgetItem(fileType.capitalize())
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

            # Pending Action
            pendingAction = file['Pending_Action']

            path = ""
            if(pendingAction == "edit"):
                path = os.path.join(interop.getIconPath(), "File0440.png")
            elif(pendingAction == "add"):
                path = os.path.join(interop.getIconPath(), "File0242.png")
            elif(pendingAction == "delete"):
                path = os.path.join(interop.getIconPath(), "File0253.png")

            widget = QtWidgets.QWidget()

            icon = QtGui.QPixmap(path)
            icon = icon.scaled(16, 16)

            iconLabel = QtWidgets.QLabel()
            iconLabel.setPixmap(icon)
            textLabel = QtWidgets.QLabel(pendingAction.capitalize())

            layout = QtWidgets.QHBoxLayout()
            layout.addWidget(iconLabel)
            layout.addWidget(textLabel)
            layout.setAlignment(QtCore.Qt.AlignLeft)
            # layout.setContentsMargins(0,0,0,0)
            widget.setLayout(layout)

            self.tableWidget.setCellWidget(i, column, widget)
            column += 1

            # Folder
            newItem = QtWidgets.QTableWidgetItem(file['Folder'])
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setStretchLastSection(True)

    def create_layout(self):
        '''
        Create the layouts and add widgets
        '''
        check_box_layout = QtWidgets.QHBoxLayout()
        check_box_layout.setContentsMargins(2, 2, 2, 2)

        main_layout = QtWidgets.QVBoxLayout()
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
            QtWidgets.QMessageBox.warning(
                interop.main_parent_window(), "Submit Warning", "No valid description entered")
            return

        files = []
        for i in range(self.tableWidget.rowCount()):
            cellWidget = self.tableWidget.cellWidget(i, 0)
            if cellWidget.findChild(QtWidgets.QCheckBox).checkState() == QtCore.Qt.Checked:
                files.append(self.fileList[i]['File'])

        keepCheckedOut = self.chkboxLockedWidget.checkState()

        progress = SubmitProgressUI(len(files))
        progress.create("Submit Progress")

        callback = TestOutputAndProgress(progress)

        progress.show()

        # self.p4.progress = callback
        # self.p4.handler = callback

        # Remove student setting from Maya .ma files
        # @ToDo make this a generic callback
        # for submitFile in files:
        #     if ".ma" in submitFile:
        #         try:
        #             pathData = self.p4.run_where(submitFile)[0]
        #             Utils.removeStudentTag(pathData['path'])
        #         except P4Exception as e:
        #             print e


        try:
            CmdsChangelist.submitChange(self.p4, files, str(
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