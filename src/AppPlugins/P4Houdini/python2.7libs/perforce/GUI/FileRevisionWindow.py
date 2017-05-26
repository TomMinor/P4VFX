import os
import sys
from P4 import P4, P4Exception
from qtpy import QtCore, QtGui, QtWidgets

from perforce import Utils
from perforce.PerforceUtils import CmdsChangelist
from perforce.AppInterop import interop
from ErrorMessageWindow import displayErrorUI
import DepotClientViewModel

class BaseRevisionTab(QtWidgets.QWidget):
    def __init__(self, p4, parent=None):
        super(BaseRevisionTab, self).__init__(parent)

        self.p4 = p4

        path = os.path.join(interop.getIconPath(), "p4.png")
        icon = QtGui.QIcon(path)

        self.setWindowTitle("File Revisions")
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.Window)

        self.fileRevisions = []

    def create(self):
        self.create_controls()
        self.create_layout()
        self.create_connections()

    def setRoot(self, root):
        self.root = root
        self.model = DepotClientViewModel.PerforceItemModel(self.p4)
        self.model.populate(self.root)

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

        self.getRevisionBtn.setVisible(False)
        self.getLatestBtn.setVisible(False)
        self.getPreviewBtn.setVisible(False)

        # self.root = "//{0}".format(self.p4.client)
        # self.root = "//depot"
        # self.model = DepotClientViewModel.PerforceItemModel(self.p4)
        # self.model.populate(self.root, showDeleted=False)
        # self.model.populate('//depot', showDeleted=True)

        self.fileTree = QtWidgets.QTreeView()
        self.fileTree.expandAll()
        # self.fileTree.setModel(self.model)

        self.fileTree.setColumnWidth(0, 220)
        self.fileTree.setColumnWidth(1, 100)
        self.fileTree.setColumnWidth(2, 120)
        self.fileTree.setColumnWidth(3, 60)

        self.fileTree.setModel(self.model)
        # self.fileTree.setRootIndex(self.model.index(self.p4.cwd))
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
        # self.horizontalLine.setFrameShape(QtWidgets.QFrame.Shape.HLine)

        if interop.getCurrentSceneFile():
            # self.fileTree.setCurrentIndex(self.model.index(interop.getCurrentSceneFile()))
            self.populateFileRevisions()

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
        self.fileTree.clicked.connect(self.populateFileRevisions)
        self.fileTree.expanded.connect(self.onExpandedFolder)
        self.getLatestBtn.clicked.connect(self.onSyncLatest)
        self.getRevisionBtn.clicked.connect(self.onRevertToSelection)
        self.getPreviewBtn.clicked.connect(self.getPreview)

    #--------------------------------------------------------------------------
    # SLOTS
    #--------------------------------------------------------------------------
    def onExpandedFolder(self, *args):
        index = args[0]

        treeItem = index.internalPointer()

        Utils.p4Logger().debug('Expanding %s...' % treeItem.data[-1])

        if not index.child(0,0).isValid():
            Utils.p4Logger().debug('\tLoading empty directory')
            self.model.populateSubDir(index, self.root)

        self.fileTree.setModel(self.model)
        self.model.layoutChanged.emit()

    def getPreview(self, *args):
        index = self.tableWidget.currentRow()
        item = self.fileRevisions[index]
        revision = item['revision']

        data = self.getSelectedTreeItemData()
        if not data:
            return
        
        # Full path is stored in the final column
        filePath = data[-1]
        fileName = data[0]

        path = os.path.join(interop.getTempPath(), fileName)

        try:
            tmpPath = path
            self.p4.run_print("-o", tmpPath, "{0}#{1}".format(filePath, revision))
            Utils.p4Logger().info("Synced preview to {0} at revision {1}".format(tmpPath, revision))
            if self.isSceneFile:
                interop.openScene(tmpPath)
            else:
                Utils.open_file(tmpPath)

        except P4Exception as e:
            displayErrorUI(e)

    def clearRevisions(self):
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)

    def getSelectedTreeItemData(self):
        index = self.fileTree.selectedIndexes()[0]
        if not index.isValid():
            return None
        
        return index.internalPointer().data

    def onRevertToSelection(self, *args):
        index = self.tableWidget.rowCount() - 1
        item = self.fileRevisions[index]
        currentRevision = item['revision']

        index = self.tableWidget.currentRow()
        item = self.fileRevisions[index]
        rollbackRevision = item['revision']

        data = self.getSelectedTreeItemData()
        if not data:
            return
        
        # Full path is stored in the final column
        filePath = data[-1]

        Utils.p4Logger().debug(filePath)

        desc = "Rollback #{0} to #{1}".format(currentRevision, rollbackRevision)
        if CmdsChangelist.syncPreviousRevision(self.p4, filePath, rollbackRevision, desc):
            QtWidgets.QMessageBox.information(interop.main_parent_window(), "Success", "Successful {0}".format(desc))

        self.populateFileRevisions()

    def onSyncLatest(self, *args):
        data = self.getSelectedTreeItemData()
        if not data:
            return

        # Full path is stored in the final column
        filePath = data[-1]

        try:
            self.p4.run_sync("-f", filePath)
            Utils.p4Logger().info("{0} synced to latest version".format(filePath))
            self.populateFileRevisions()
        except P4Exception as e:
            displayErrorUI(e)

    def setRevisionTableColumn(self, row, column, value, icon=None, isLongText=False):
        value = str(value)

        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignHCenter)

        # Use a QLineEdit to allow the text to be copied if the data is large
        if isLongText:
            textLabel = QtWidgets.QLineEdit()
            textLabel.setText(value)
            textLabel.setCursorPosition(0)
            textLabel.setReadOnly(True)
            textLabel.setStyleSheet("QLineEdit { border: none }")
        else:
            textLabel = QtWidgets.QLabel(value)
            textLabel.setStyleSheet("QLabel { border: none } ")

        # layout.setContentsMargins(4, 0, 4, 0)
        
        if icon:
            iconPic = QtGui.QPixmap(icon)
            iconPic = iconPic.scaled(16, 16)
            iconLabel = QtWidgets.QLabel()
            iconLabel.setPixmap(iconPic)
            layout.addWidget(iconLabel)
        layout.addWidget(textLabel)

        widget.setLayout(layout)

        self.tableWidget.setCellWidget(row, column, widget)

    def populateFileRevisions(self, *args):
        self.statusBar.showMessage("")

        try:
            index = self.fileTree.selectedIndexes()
        except IndexError as e:
            Utils.p4Logger().error(e)
            raise

        if not index or not index[0].internalPointer().data:
            return
        index = index[0]

        try:
            name, filetype, time, action, change, fullname = index.internalPointer().data
        except ValueError as e:
            Utils.p4Logger().info(index.internalPointer().data)
            raise e


        self.getRevisionBtn.setEnabled(False)
        self.getLatestBtn.setEnabled(False)
        self.getPreviewBtn.setEnabled(False)

        if filetype == 'Folder':
            self.getRevisionBtn.setVisible(False)
            self.getLatestBtn.setVisible(False)
            self.getPreviewBtn.setVisible(False)
            self.isSceneFile = False
            self.clearRevisions()
            return
        else:
            self.getRevisionBtn.setVisible(True)
            self.getLatestBtn.setVisible(True)
            self.getPreviewBtn.setVisible(True)

        if Utils.queryFileExtension(fullname, interop.getSceneFiles() ):
            self.getPreviewBtn.setEnabled(True)
            self.getPreviewBtn.setText("Preview Scene Revision")
            self.isSceneFile = True
        else:
            self.getPreviewBtn.setText("Preview File Revision")
            self.isSceneFile = False


        try:
            with self.p4.at_exception_level(P4.RAISE_ERRORS):
                files = self.p4.run_filelog("-l", fullname)
        except P4Exception as e:
            # TODO - Better error handling here, what if we can't connect etc
            #eMsg, type = parsePerforceError(e)
            self.statusBar.showMessage("{0} isn't on client".format(os.path.basename(fullname)))
            self.clearRevisions()
            self.getLatestBtn.setEnabled(False)
            self.getPreviewBtn.setEnabled(False)
            return

        self.getLatestBtn.setEnabled(True)
        self.getPreviewBtn.setEnabled(True)

        try:
            with self.p4.at_exception_level(P4.RAISE_ERRORS):
                p4FileInfo = self.p4.run_fstat(fullname)

            if p4FileInfo:
                fileInfo = p4FileInfo[0]
                
                if 'otherLock' in fileInfo:
                    self.statusBar.showMessage("{0} currently locked by {1}".format(os.path.basename(fullname), fileInfo['otherLock'][0]))

                    if fileInfo['otherLock'][0].split('@')[0] != self.p4.user:
                        self.getRevisionBtn.setEnabled(False)
                elif 'otherOpen' in fileInfo:
                    self.statusBar.showMessage("{0} currently opened by {1}".format(os.path.basename(fullname), fileInfo['otherOpen'][0]))

                    if fileInfo['otherOpen'][0].split('@')[0] != self.p4.user:
                        self.getRevisionBtn.setEnabled(False)
                else:
                    self.statusBar.showMessage("{0} currently opened by {1}@{2}".format(os.path.basename(fullname),  self.p4.user, self.p4.client))
                    self.getRevisionBtn.setEnabled(True)

        except P4Exception:
            self.statusBar.showMessage("{0} is not checked out".format(os.path.basename(fullname)))
            self.getRevisionBtn.setEnabled(True)

        # Generate revision dictionary
        self.fileRevisions = []

        if files:
            Utils.p4Logger().debug( 'filelog(%s):%s' % (fullname, files) )

            for revision in files[0].each_revision():
                self.fileRevisions.append({"revision": revision.rev,
                                           "action": revision.action,
                                           "date": revision.time,
                                           "desc": revision.desc,
                                           "user": revision.user,
                                           "client": revision.client
                                           })

            self.tableWidget.setRowCount(len(self.fileRevisions))

            # Map a file action to the path of it's UI icon
            actionToIcon = {
                    'edit':         os.path.join(interop.getIconPath(), "File0440.png"),
                    'add':          os.path.join(interop.getIconPath(), "File0242.png"),
                    'delete':       os.path.join(interop.getIconPath(), "File0253.png"),
                    'move/delete':  os.path.join(interop.getIconPath(), "File0253.png"),
                    'purge':        os.path.join(interop.getIconPath(), "File0253.png")
                }

            # Populate table
            for i, revision in enumerate(self.fileRevisions):
                columns = [ 
                        ("#{0}".format(revision['revision']), None, False),
                        (revision['user'],  None, False),
                        (revision['action'].capitalize(), actionToIcon.get(revision['action']), False),
                        (revision['date'], None, False),
                        (revision['client'], None, False),
                        (revision['desc'], None, True)
                    ]

                for j, data in enumerate(columns):
                    self.setRevisionTableColumn(i, j, *data)

        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.horizontalHeader().setStretchLastSection(True)

class ClientRevisionTab(BaseRevisionTab):
    def __init__(self, p4, parent=None):
        super(ClientRevisionTab, self).__init__(p4, parent)

        # self.setRoot( "//{0}".format(self.p4.client) )
        self.setRoot( self.p4.run_info()[0]['clientRoot'].replace('\\', '/') )

class DepotRevisionTab(BaseRevisionTab):
    def __init__(self, p4, parent=None):
        super(DepotRevisionTab, self).__init__(p4, parent)

        self.setRoot( "//depot" )

class FileRevisionUI(QtWidgets.QWidget):
    def __init__(self, p4, parent=None):
        super(FileRevisionUI, self).__init__(parent)

        self.p4 = p4

        path = os.path.join(interop.getIconPath(), "p4.png")
        icon = QtGui.QIcon(path)

        self.setWindowTitle("File Revisions")
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.Window)

        self.fileRevisions = []

    def create(self):
        self.create_controls()
        self.create_layout()
        self.create_connections()

    def create_controls(self):
        '''
        Create the widgets for the dialog
        '''
        self.tabwidget = QtWidgets.QTabWidget()
        self.clientTab = ClientRevisionTab(self.p4)
        self.clientTab.create()
        self.depotTab = DepotRevisionTab(self.p4)
        self.depotTab.create()
        self.tabwidget.addTab( self.clientTab, 'Client' )
        self.tabwidget.addTab( self.depotTab , 'Depot' )

    def create_layout(self):
        '''
        Create the layouts and add widgets
        '''
        check_box_layout = QtWidgets.QHBoxLayout()
        check_box_layout.setContentsMargins(2, 2, 2, 2)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.addWidget(self.tabwidget)

        # main_layout.addLayout(bottomLayout)
        # main_layout.addWidget(self.horizontalLine)
        # main_layout.addWidget(self.statusBar)

        self.setLayout(main_layout)

    def create_connections(self):
        '''
        Create the signal/slot connections
        '''
        pass
        # self.fileTree.clicked.connect(self.populateFileRevisions)
        # self.fileTree.expanded.connect(self.onExpandedFolder)
        # self.getLatestBtn.clicked.connect(self.onSyncLatest)
        # self.getRevisionBtn.clicked.connect(self.onRevertToSelection)
        # self.getPreviewBtn.clicked.connect(self.getPreview)