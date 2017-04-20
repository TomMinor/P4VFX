from P4 import P4, P4Exception

from Qt import QtCore, QtGui, QtWidgets

import perforce.Utils as Utils
import GUI.DepotClientViewModel
from perforce.DCCInterop import interop

def fullPath(idx):
    result = [idx]

    parent = idx.parent()
    while True:
        if not parent.isValid():
            break
        result.append(parent)
        parent = parent.parent()

    return list(reversed(result))

class FileRevisionUI(QtGui.QDialog):

    def __init__(self, parent=interop.main_parent_window()):
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

    def populateSubDir(self, idx, root="//depot", findDeleted=False):
        idxPathModel = fullPath(idx)
        idxPathSubDirs = [idxPath.data() for idxPath in idxPathModel]
        idxFullPath = os.path.join(*idxPathSubDirs)

        if not idxFullPath:
            idxFullPath = "."

        # children = []

        p4path = '/'.join([root, idxFullPath, '*'])

        depotPath = False
        if "depot" in root:
            depotPath = True

        if depotPath:
            p4subdirs = self.p4.run_dirs(p4path)
        else:
            p4subdirs = self.p4.run_dirs('-H', p4path)

        p4subdir_names = [child['dir'] for child in p4subdirs]

        treeItem = idx.internalPointer()

        # print idx.child(0,0).data(), p4subidrs

        if not idx.child(0, 0).data() and p4subdirs:
            # Pop empty "None" child
            treeItem.popChild()

            for p4child in p4subdir_names:
                print p4child
                data = [os.path.basename(p4child), "Folder", "", "", ""]

                childData = TreeItem(data, treeItem)
                treeItem.appendChild(childData)

                childData.appendChild(None)

                files = DepotClientViewModel.p4Filelist(self.p4, p4child, findDeleted)

                for f in files:
                    fileName = os.path.basename(f['name'])
                    data = [fileName, f['type'], f[
                        'time'], f['action'], f['change']]

                    fileData = TreeItem(data, childData)
                    childData.appendChild(fileData)


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
        print p4path
        p4children = self.p4.run_dirs("-H", p4path)
        p4children_names = [child['dir'] for child in p4children]

        if idx.child(0, 0).data() == "TMP":
            for p4child in p4children_names:
                data = [p4child, "", "", ""]
                childData = TreeItem(data, idx)
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
            childDir = TreeItem(data, childIdx)
            childIdx.appendChild(childDir)

            tmpDir = TreeItem(["TMP", "", "", "", ""], childDir)
            childDir.appendChild(tmpDir)

        # view.setModel(model)

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

        model = TreeModel(self.p4)
        # model.populate("//{0}".format(self.p4.client), findDeleted=True)
        model.populate('//depot', findDeleted=True)

        self.fileTree = QtGui.QTreeView()
        self.fileTree.expandAll()
        self.fileTree.setModel(model)

        for i in range(model.rootrowcount()):
            idx = model.index(i, 0, model.parent(QtCore.QModelIndex()))

            treeItem = idx.internalPointer()

            self.populateSubDir(idx)

            # test = TreeItem( ["TEST", "", "", ""], treeItem  )
            # treeItem.appendChild( test )

        self.fileTree.setColumnWidth(0, 220)
        self.fileTree.setColumnWidth(1, 100)
        self.fileTree.setColumnWidth(2, 120)
        self.fileTree.setColumnWidth(3, 60)

        # self.fileTree.setModel(self.fileTreeModel)
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
        self.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

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
            Utils.p4Logger().info(
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
                interop.main_parent_window(), "Success", "Successful {0}".format(desc))

        self.loadFileLog()

    def onSyncLatest(self, *args):
        index = self.fileTree.selectedIndexes()[0]
        if not index:
            return

        filePath = self.fileTreeModel.fileInfo(index).absoluteFilePath()

        try:
            self.p4.run_sync("-f", filePath)
            Utils.p4Logger().info("{0} synced to latest version".format(filePath))
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