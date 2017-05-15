import os
import sys

from P4 import P4, P4Exception
from Qt import QtCore, QtGui, QtWidgets

import perforce.Utils as Utils
import DepotClientViewModel
from perforce.AppInterop import interop

def fullPath(idx):
    result = [idx]

    parent = idx.parent()
    while True:
        if not parent.isValid():
            break
        result.append(parent)
        parent = parent.parent()

    return list(reversed(result))

class FileRevisionUI(QtWidgets.QDialog):

    def __init__(self, parent=interop.main_parent_window()):
        super(FileRevisionUI, self).__init__(parent)

    def create(self, p4, files=[]):
        self.p4 = p4

        path = interop.getIconPath() + "p4.png"
        icon = QtGui.QIcon(path)

        self.setWindowTitle("File Revisions")
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.Window)

        self.fileRevisions = []

        self.create_controls()
        self.create_layout()
        self.create_connections()

    def tmp(self, *args):
        idx = args[0]

        children = []

        i = 1
        while True:
            child = idx.child(i, 0)
            print i, child.data()
            if not child.isValid():
                break

            children.append(child)
            i += 1

            self.populateSubDir(child, findDeleted=False)

        return

        treeItem = idx.internalPointer()

        idxPathModel = fullPath(idx, model.showDeleted)

        idxPathSubDirs = [idxPath.data() for idxPath in idxPathModel]
        idxFullPath = os.path.join(*idxPathSubDirs)
        pathDepth = len(idxPathSubDirs)

        children = []

        p4path = "//{0}/{1}/*".format(self.p4.client, idxFullPath)
        Utils.p4Logger().debug(p4path)
        p4children = self.p4.run_dirs("-H", p4path)
        p4children_names = [child['dir'] for child in p4children]

        if idx.child(0, 0).data() == "TMP":
            for p4child in p4children_names:
                data = [p4child, "", "", ""]
                childData = DepotClientViewModel.TreeItem(data, idx)
                treeItem.appendChild(childData)

        i = 0
        while True:
            child = idx.child(i, 0)
            if not child.isValid():
                break

            children.append(child)
            i += 1

        for child in children:
            childIdx = child.internalPointer()

            data = ["TEST", "TEST", "TEST", "TEST"]
            childDir = DepotClientViewModel.TreeItem(data, childIdx)
            childIdx.appendChild(childDir)

            tmpDir = DepotClientViewModel.TreeItem(["TMP", "", "", "", ""], childDir)
            childDir.appendChild(tmpDir)

        # view.setModel(model)

    def create_controls(self):
        '''
        Create the widgets for the dialog
        '''
        self.descriptionWidget = QtWidgets.QPlainTextEdit("<Enter Description>")
        self.descriptionLabel = QtWidgets.QLabel("Change Description:")
        self.getRevisionBtn = QtWidgets.QPushButton("Revert to Selected Revision")
        self.getLatestBtn = QtWidgets.QPushButton("Sync to Latest Revision")
        self.getPreviewBtn = QtWidgets.QPushButton("Preview Scene")
        self.getPreviewBtn.setEnabled(False)

        self.fileTreeModel = QtWidgets.QFileSystemModel()
        self.fileTreeModel.setRootPath(self.p4.cwd)

        model = DepotClientViewModel.TreeModel(self.p4)
        model.populate("//{0}".format(self.p4.client), findDeleted=True)
        # model.populate('//depot', findDeleted=True)

        self.fileTree = QtWidgets.QTreeView()
        self.fileTree.expandAll()
        self.fileTree.setModel(model)

        for i in range(model.rootrowcount()):
            idx = model.index(i, 0, model.parent(QtCore.QModelIndex()))

            treeItem = idx.internalPointer()

            model.populateSubDir(idx)

            # test = DepotClientViewModel.TreeItem( ["TEST", "", "", ""], treeItem  )
            # treeItem.appendChild( test )

        self.fileTree.setColumnWidth(0, 220)
        self.fileTree.setColumnWidth(1, 100)
        self.fileTree.setColumnWidth(2, 120)
        self.fileTree.setColumnWidth(3, 60)

        self.fileTree.setModel(model)
        self.fileTree.setRootIndex(self.fileTreeModel.index(self.p4.cwd))
        self.fileTree.setColumnWidth(0, 180)

        headers = ["Revision", "User", "Action",
                   "Date", "Client", "Description"]

        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setMaximumHeight(200)
        self.tableWidget.setMinimumWidth(500)
        self.tableWidget.setHorizontalHeaderLabels(headers)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.statusBar = QtWidgets.QStatusBar()
        # self.statusBar.showMessage("Test")

        self.horizontalLine = QtWidgets.QFrame()
        self.horizontalLine.setFrameShape(QtWidgets.QFrame.Shape.HLine)

        if interop.getCurrentSceneFile():
            self.fileTree.setCurrentIndex(self.fileTreeModel.index(interop.getCurrentSceneFile()))
            self.loadFileLog()

    def create_layout(self):
        '''
        Create the layouts and add widgets
        '''
        check_box_layout = QtWidgets.QHBoxLayout()
        check_box_layout.setContentsMargins(2, 2, 2, 2)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)

        main_layout.addWidget(self.fileTree)
        main_layout.addWidget(self.tableWidget)

        bottomLayout = QtWidgets.QHBoxLayout()
        bottomLayout.addWidget(self.getRevisionBtn)
        bottomLayout.addSpacerItem(QtWidgets.QSpacerItem(20, 16))
        bottomLayout.addWidget(self.getPreviewBtn)
        bottomLayout.addSpacerItem(QtWidgets.QSpacerItem(20, 16))
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
            Utils.p4Logger().info(
                "Synced preview to {0} at revision {1}".format(tmpPath, revision))
            if self.isSceneFile:
                interop.openScene(tmpPath)
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
            QtWidgets.QMessageBox.information(
                interop.main_parent_window(), "Success", "Successful {0}".format(desc))

        self.loadFileLog()

    def onSyncLatest(self, *args):
        try:
            index = self.fileTree.selectedIndexes()[0]
            if not index:
                return
        except IndexError as e:
            Utils.p4Logger().info(e)
            return

        filePath = self.fileTreeModel.fileInfo(index).absoluteFilePath()

        try:
            self.p4.run_sync("-f", filePath)
            Utils.p4Logger().info("{0} synced to latest version".format(filePath))
            self.loadFileLog()
        except P4Exception as e:
            displayErrorUI(e)

    def loadFileLog(self, *args):
        try:
            index = self.fileTree.selectedIndexes()[0]
            if not index:
                return
        except IndexError as e:
            Utils.p4Logger().error(e)
            return

        self.statusBar.showMessage("")


        self.getPreviewBtn.setEnabled(True)

        if not index.internalPointer().data:
            return
        
        try:
            name, filetype, time, action, change, fullname = index.internalPointer().data
        except ValueError as e:
            Utils.p4Logger().info(index.internalPointer().data)
            raise e
        # filePath = self.fileTreeModel.fileInfo(index).absoluteFilePath()
        # Utils.p4Logger().debug('Querying history for file %s' % filePath)

        if Utils.queryFileExtension(fullname, interop.getSceneFiles() ):
            # self.getPreviewBtn.setEnabled(True)
            self.getPreviewBtn.setText("Preview Scene Revision")
            self.isSceneFile = True
        else:
            # self.getPreviewBtn.setEnabled(False)
            self.getPreviewBtn.setText("Preview File Revision")
            self.isSceneFile = False

        # if os.path.isdir(filePath):
            # return

        if filetype == 'Folder':
            return
            # self.populateSubDir(index, fullname, False)
        else:
            try:
                files = self.p4.run_filelog("-l", fullname)
            except P4Exception as e:
                # TODO - Better error handling here, what if we can't connect etc
                #eMsg, type = parsePerforceError(e)
                self.statusBar.showMessage(
                    "{0} isn't on client".format(os.path.basename(fullname)))
                self.tableWidget.clearContents()
                self.getLatestBtn.setEnabled(False)
                self.getPreviewBtn.setEnabled(False)
                return

            self.getLatestBtn.setEnabled(True)
            self.getPreviewBtn.setEnabled(True)

            try:
                fileInfo = self.p4.run_fstat(fullname)
                print fileInfo
                if fileInfo:
                    if 'otherLock' in fileInfo[0]:
                        self.statusBar.showMessage("{0} currently locked by {1}".format(
                            os.path.basename(fullname), fileInfo[0]['otherLock'][0]))
                        if fileInfo[0]['otherLock'][0].split('@')[0] != self.p4.user:
                            self.getRevisionBtn.setEnabled(False)
                    elif 'otherOpen' in fileInfo[0]:
                        self.statusBar.showMessage("{0} currently opened by {1}".format(
                            os.path.basename(fullname), fileInfo[0]['otherOpen'][0]))
                        if fileInfo[0]['otherOpen'][0].split('@')[0] != self.p4.user:
                            self.getRevisionBtn.setEnabled(False)
                    else:
                        self.statusBar.showMessage("{0} currently opened by {1}@{2}".format(
                            os.path.basename(fullname),  self.p4.user, self.p4.client))
                        self.getRevisionBtn.setEnabled(True)

            except P4Exception:
                self.statusBar.showMessage("{0} is not checked out".format(os.path.basename(fullname)))
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

                widget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout()
                label = QtWidgets.QLabel(str(change))

                layout.addWidget(label)
                layout.setAlignment(QtCore.Qt.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                widget.setLayout(layout)

                self.tableWidget.setCellWidget(i, column, widget)
                column += 1

                # User
                user = revision['user']

                widget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout()
                label = QtWidgets.QLabel(str(user))
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
                textLabel.setStyleSheet("QLabel { border: none } ")

                # @TODO Why not move these into a cute little function in a function

                layout = QtWidgets.QHBoxLayout()
                layout.addWidget(iconLabel)
                layout.addWidget(textLabel)
                layout.setAlignment(QtCore.Qt.AlignLeft)
                # layout.setContentsMargins(0,0,0,0)
                widget.setLayout(layout)

                self.tableWidget.setCellWidget(i, column, widget)
                column += 1

                # Date
                date = revision['date']

                widget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout()
                label = QtWidgets.QLabel(str(date))
                label.setStyleSheet("QLabel { border: none } ")

                layout.addWidget(label)
                layout.setAlignment(QtCore.Qt.AlignCenter)
                layout.setContentsMargins(4, 0, 4, 0)
                widget.setLayout(layout)

                self.tableWidget.setCellWidget(i, column, widget)
                column += 1

                # Client
                client = revision['client']

                widget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout()
                label = QtWidgets.QLabel(str(client))
                label.setStyleSheet("QLabel { border: none } ")

                layout.addWidget(label)
                layout.setAlignment(QtCore.Qt.AlignCenter)
                layout.setContentsMargins(4, 0, 4, 0)

                widget.setLayout(layout)

                self.tableWidget.setCellWidget(i, column, widget)
                column += 1

                # Description
                desc = revision['desc']

                widget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout()
                text = QtWidgets.QLineEdit()
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