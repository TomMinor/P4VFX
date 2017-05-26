import os

from P4 import P4, P4Exception
from qtpy import QtCore, QtGui, QtWidgets

import perforce.Utils as Utils
from perforce.AppInterop import interop

class OpenedFilesUI(QtWidgets.QDialog):

    def __init__(self, parent=interop.main_parent_window()):
        super(OpenedFilesUI, self).__init__(parent)

    def create(self, p4, files=[]):
        self.p4 = p4

        path = interop.getIconPath()
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

        self.tableWidget = QtWidgets.QTableWidget(0, len(headers))
        self.tableWidget.setMaximumHeight(200)
        self.tableWidget.setMinimumWidth(500)
        self.tableWidget.setHorizontalHeaderLabels(headers)
        self.tableWidget.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection)


        self.openSelectedBtn = QtWidgets.QPushButton("Open")
        self.openSelectedBtn.setEnabled(False)
        self.openSelectedBtn.setIcon(QtGui.QIcon(
            os.path.join(interop.getIconPath(), "File0228.png")))

        self.revertFileBtn = QtWidgets.QPushButton("Remove from changelist")
        self.revertFileBtn.setEnabled(False)
        self.revertFileBtn.setIcon(QtGui.QIcon(
            os.path.join(interop.getIconPath(), "File0308.png")))

        self.refreshBtn = QtWidgets.QPushButton("Refresh")
        self.refreshBtn.setIcon(QtGui.QIcon(
            os.path.join(interop.getIconPath(), "File0175.png")))

        self.updateTable()

    def create_layout(self):
        '''
        Create the layouts and add widgets
        '''
        check_box_layout = QtWidgets.QHBoxLayout()
        check_box_layout.setContentsMargins(2, 2, 2, 2)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)

        main_layout.addWidget(self.tableWidget)

        bottomLayout = QtWidgets.QHBoxLayout()
        bottomLayout.addWidget(self.revertFileBtn)
        bottomLayout.addWidget(self.refreshBtn)
        bottomLayout.addSpacerItem(QtWidgets.QSpacerItem(400, 16))
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
            Utils.p4Logger().info(self.p4.run_revert("-k", depotFile))
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

            if Utils.queryFileExtension(depotFile, interop.getSceneFiles()):
                interop.openScene(clientFile)
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

            # User
            fileType = file['User']
            newItem = QtWidgets.QTableWidgetItem(fileType)
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

            # Folder
            newItem = QtWidgets.QTableWidgetItem(file['Folder'])
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tableWidget.setItem(i, column, newItem)
            column += 1

        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setStretchLastSection(True)