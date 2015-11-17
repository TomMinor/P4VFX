import traceback
import os
import logging
import ntpath

from PySide import QtCore
from PySide import QtGui

from P4 import P4, P4Exception

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken import wrapInstance

# Hacky way to load our icons, I don't fancy wrestling with resource files
iconPath = os.environ['MAYA_APP_DIR'] + "/scripts/images/"
tempPath = os.environ['TMPDIR']

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)

def getCurrentSceneFile():
    return cmds.file(q=True, sceneName=True)
    
def openScene(filePath):
    cmds.file(filePath, f=True, o=True)
    
mainParent = maya_main_window()

def parsePerforceError(e):
    eMsg = str(e).replace("[P4#run]", "")
    idx = eMsg.find('\t')
    firstPart = " ".join(eMsg[0:idx].split())
    firstPart = firstPart[:-1]
    
    secondPart = eMsg[idx:]
    secondPart = secondPart.replace('\\n', '\n')
    secondPart = secondPart.replace('"', '')
    secondPart = " ".join(secondPart.split())
    secondPart = secondPart.replace(' ', '', 1) # Annoying space at the start, remove it
    
    eMsg = "{0}\n\n{1}".format(firstPart, secondPart)

    type = "info"
    if "[Warning]" in str(e):
        eMsg = eMsg.replace("[Warning]:", "")
        type = "warning"
    elif "[Error]" in str(e):
        eMsg = eMsg.replace("[Error]:", "")
        type = "error"
    
    return eMsg, type

def displayErrorUI(e):
    error_ui = QtGui.QMessageBox()
    error_ui.setWindowFlags(QtCore.Qt.WA_DeleteOnClose)
    
    eMsg, type = parsePerforceError(e)
    
    if type == "warning":
        error_ui.warning(mainParent, "Submit Warning", eMsg)
    elif type == "error":
        error_ui.critical(mainParent, "Submit Error", eMsg)
    else:
        error_ui.information(mainParent, "Submit Error", eMsg)
        
    error_ui.deleteLater()  

class SubmitChangeUi(QtGui.QDialog):
    def __init__(self, parent=mainParent ):
        super(SubmitChangeUi, self).__init__(parent)
        
    def create(self, files = [] ):
        self.p4 = p4
        
        path = iconPath + "p4.png"
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
         
        headers = [ " ", "File", "Type", "Action", "Folder" ]
        
        self.tableWidget = QtGui.QTableWidget( len(self.fileList), len(headers) )
        self.tableWidget.setMaximumHeight(200)
        self.tableWidget.setMinimumWidth(500)
        self.tableWidget.setHorizontalHeaderLabels( headers )
        
        
        for i, file in enumerate(self.fileList):
            # Saves us manually keeping track of the current column
            column = 0
            
            # Create checkbox in first column
            widget = QtGui.QWidget()
            layout = QtGui.QHBoxLayout()
            chkbox = QtGui.QCheckBox()
            chkbox.setCheckState(QtCore.Qt.Checked)
            
            layout.addWidget( chkbox )
            layout.setAlignment(QtCore.Qt.AlignCenter)
            layout.setContentsMargins(0,0,0,0)
            widget.setLayout(layout)
            
            self.tableWidget.setCellWidget(i, column, widget)
            column += 1

            # Fill in the rest of the data
            # File
            fileName = file['File']
            newItem = QtGui.QTableWidgetItem( os.path.basename(fileName) )
            newItem.setFlags( newItem.flags() ^ QtCore.Qt.ItemIsEditable )
            self.tableWidget.setItem(i, column, newItem) 
            column += 1
            
            # Text
            fileType = file['Type']
            newItem = QtGui.QTableWidgetItem( fileType.capitalize() )
            newItem.setFlags( newItem.flags() ^ QtCore.Qt.ItemIsEditable )
            self.tableWidget.setItem(i, column, newItem) 
            column += 1
            
            # Pending Action
            pendingAction = file['Pending_Action']
            
            path = ""
            if( pendingAction == "edit" ):
                path = iconPath + "icon_blue.png"
            elif( pendingAction == "add" ):
                path = iconPath + "icon_green.png"
            elif( pendingAction == "delete" ):
                path = iconPath + "icon_red.png"

            widget = QtGui.QWidget()

            icon = QtGui.QPixmap(path)
            icon = icon.scaled(16, 16)
            
            iconLabel = QtGui.QLabel()
            iconLabel.setPixmap(icon)
            textLabel = QtGui.QLabel( pendingAction.capitalize() )
            
            layout = QtGui.QHBoxLayout()
            layout.addWidget( iconLabel )
            layout.addWidget( textLabel )
            layout.setAlignment(QtCore.Qt.AlignLeft)
            #layout.setContentsMargins(0,0,0,0)
            widget.setLayout(layout)
            
            self.tableWidget.setCellWidget(i, column, widget)
            column += 1
            
            # Folder
            newItem = QtGui.QTableWidgetItem( file['Folder'])
            newItem.setFlags( newItem.flags() ^ QtCore.Qt.ItemIsEditable )
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
        
        #main_layout.addStretch()
        
        self.setLayout(main_layout)
                
    def create_connections(self):
        '''
        Create the signal/slot connections
        '''        
        self.submitBtn.clicked.connect(self.on_submit)
        self.descriptionWidget.textChanged.connect(self.on_text_changed)
        
        
    #--------------------------------------------------------------------------
    # SLOTS
    #--------------------------------------------------------------------------      
    def on_submit(self):
        if not self.validateText():
            QtGui.QMessageBox.warning(mainParent, "Submit Warning", "No valid description entered")
            return
        
        files = []
        for i in range( self.tableWidget.rowCount() ):
            cellWidget = self.tableWidget.cellWidget(i, 0)
            if cellWidget.findChild( QtGui.QCheckBox ).checkState() == QtCore.Qt.Checked:
                files.append( self.fileList[i]['File'] )
                
        keepCheckedOut = self.chkboxLockedWidget.checkState()
                
        try:
            submitChange(files, str(self.descriptionWidget.toPlainText()), keepCheckedOut )
            self.close()
        except P4Exception as e:
            displayErrorUI(e)

    def validateText(self):
        text = self.descriptionWidget.toPlainText()
        p = QtGui.QPalette()
        if text == "<Enter Description>" or "<" in text or ">" in text:
            p.setColor(QtGui.QPalette.Active,   QtGui.QPalette.Text, QtCore.Qt.red)
            p.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Text, QtCore.Qt.red)
            self.descriptionWidget.setPalette(p)
            return False
        self.descriptionWidget.setPalette(p)
        return True
        
    def on_text_changed(self):
        self.validateText()



class OpenedFilesUI(QtGui.QDialog):
    def __init__(self, parent=mainParent ):
        super(OpenedFilesUI, self).__init__(parent)
        
    def create(self, files = [] ):
        self.p4 = p4
        
        path = iconPath + "p4.png"
        icon = QtGui.QIcon(path)
        
        self.setWindowTitle("Opened Files")
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.Window)
        
        self.fileList = files
        
        self.create_controls()
        self.create_layout()
        self.create_connections()

    def create_controls(self):
        '''
        Create the widgets for the dialog
        '''  
        headers = [ "File", "Type", "Action", "Folder" ]
        
        self.tableWidget = QtGui.QTableWidget( len(self.fileList), len(headers) )
        self.tableWidget.setMaximumHeight(200)
        self.tableWidget.setMinimumWidth(500)
        self.tableWidget.setHorizontalHeaderLabels( headers )
        
        
        for i, file in enumerate(self.fileList):
            # Saves us manually keeping track of the current column
            column = 0

            # Fill in the rest of the data
            # File
            fileName = file['File']
            newItem = QtGui.QTableWidgetItem( os.path.basename(fileName) )
            newItem.setFlags( newItem.flags() ^ QtCore.Qt.ItemIsEditable )
            self.tableWidget.setItem(i, column, newItem) 
            column += 1
            
            # Text
            fileType = file['Type']
            newItem = QtGui.QTableWidgetItem( fileType.capitalize() )
            newItem.setFlags( newItem.flags() ^ QtCore.Qt.ItemIsEditable )
            self.tableWidget.setItem(i, column, newItem) 
            column += 1
            
            # Pending Action
            pendingAction = file['Pending_Action']
            
            path = ""
            if( pendingAction == "edit" ):
                path = iconPath + "icon_blue.png"
            elif( pendingAction == "add" ):
                path = iconPath + "icon_green.png"
            elif( pendingAction == "delete" ):
                path = iconPath + "icon_red.png"

            widget = QtGui.QWidget()

            icon = QtGui.QPixmap(path)
            icon = icon.scaled(16, 16)
            
            iconLabel = QtGui.QLabel()
            iconLabel.setPixmap(icon)
            textLabel = QtGui.QLabel( pendingAction.capitalize() )
            
            layout = QtGui.QHBoxLayout()
            layout.addWidget( iconLabel )
            layout.addWidget( textLabel )
            layout.setAlignment(QtCore.Qt.AlignLeft)
            #layout.setContentsMargins(0,0,0,0)
            widget.setLayout(layout)
            
            self.tableWidget.setCellWidget(i, column, widget)
            column += 1
            
            # Folder
            newItem = QtGui.QTableWidgetItem( file['Folder'])
            newItem.setFlags( newItem.flags() ^ QtCore.Qt.ItemIsEditable )
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
        
        main_layout.addWidget(self.tableWidget)
        
        self.setLayout(main_layout)
                
    def create_connections(self):
        '''
        Create the signal/slot connections
        '''        

        
        
    #--------------------------------------------------------------------------
    # SLOTS
    #--------------------------------------------------------------------------  


class FileRevisionUI(QtGui.QDialog):
    def __init__(self, parent=mainParent ):
        super(FileRevisionUI, self).__init__(parent)
        
    def create(self, files = [] ):
        self.p4 = p4
        
        path = iconPath + "p4.png"
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
        self.fileTreeModel.setRootPath( self.p4.cwd )
        self.fileTree = QtGui.QTreeView()
        self.fileTree.setModel(self.fileTreeModel)
        self.fileTree.setRootIndex( self.fileTreeModel.index(self.p4.cwd) )
        self.fileTree.setColumnWidth(0, 180)
         
        headers = [ "Revision", "Action", "Date", "Description" ]
        
        self.tableWidget = QtGui.QTableWidget()
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setMaximumHeight(200)
        self.tableWidget.setMinimumWidth(500)
        self.tableWidget.setHorizontalHeaderLabels( headers )
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        
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
        bottomLayout.addWidget( self.getRevisionBtn )
        bottomLayout.addSpacerItem( QtGui.QSpacerItem(20, 16) )
        bottomLayout.addWidget(self.getPreviewBtn )
        bottomLayout.addSpacerItem( QtGui.QSpacerItem(20, 16) )
        bottomLayout.addWidget( self.getLatestBtn )
        
        main_layout.addLayout( bottomLayout ) 
        self.setLayout(main_layout)
                
    def create_connections(self):
        '''
        Create the signal/slot connections
        '''        
        self.fileTree.clicked.connect( self.loadFileLog )
        self.getLatestBtn.clicked.connect( self.onSyncLatest )
        self.getRevisionBtn.clicked.connect( self.onRevertToSelection )
        self.getPreviewBtn.clicked.connect( self.getPreview )

        
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
        
        try:
            tmpPath = os.path.join(tempPath, ntpath.basename(filePath))
            p4.run_print("-o", tmpPath, "{0}#{1}".format(filePath, revision))
            logging.info("Synced preview to {0} at revision {1}".format(tmpPath, revision))
            openScene(tmpPath)
        except P4Exception as e:
            displayErrorUI(e)
        
    
    def onRevertToSelection(self, *args): 
        index = self.tableWidget.currentRow()
        item = self.fileRevisions[index]
        revision = item['revision']
        
        index = self.fileTree.selectedIndexes()[0]
        if not index:
            return
        
        filePath = self.fileTreeModel.fileInfo(index).absoluteFilePath()
        
        if syncPreviousRevision(filePath, revision, "Rollback test"):
            QtGui.QMessageBox.information(mainParent, "Rollback", "Success!")
        
        self.loadFileLog()
        
        
    def onSyncLatest(self, *args):
        index = self.fileTree.selectedIndexes()[0]
        if not index:
            return
            
        filePath = self.fileTreeModel.fileInfo(index).absoluteFilePath()
        
        try:
            p4.run_sync("-f", filePath)
            logging.info("{0} synced to latest version".format(filePath))
            self.loadFileLog()
        except P4Exception as e:
            displayErrorUI(e)
    
    def loadFileLog(self, *args):    
        index = self.fileTree.selectedIndexes()[0]
        if not index:
            return
        
        filePath = self.fileTreeModel.fileInfo(index).absoluteFilePath()

        # Only support maya scene file preview
        fileExt = os.path.splitext(filePath)[1]
        if fileExt == ".ma" or fileExt == ".mb":
            self.getPreviewBtn.setEnabled(True)
        else:
            self.getPreviewBtn.setEnabled(False)
        
        if os.path.isdir(filePath):
            return
        
        files = p4.run_filelog("-l", filePath )        

        # Generate revision dictionary
        self.fileRevisions  = []

        for file in files:
            file.depotFile
            for revision in file.revisions:
                self.fileRevisions .append( { "revision": revision.rev, 
                                        "action": revision.action, 
                                        "date"  : revision.time,
                                        "desc"  : revision.desc
                                        } ) 

        self.tableWidget.setRowCount( len(self.fileRevisions ) )

        # Populate table
        for i, revision in enumerate(self.fileRevisions ):
            # Saves us manually keeping track of the current column
            column = 0

            # Fill in the rest of the data
            change = "#{0}".format(revision['revision'])
            
            widget = QtGui.QWidget()
            layout = QtGui.QHBoxLayout()
            label = QtGui.QLabel(str(change))
            
            layout.addWidget( label )
            layout.setAlignment(QtCore.Qt.AlignCenter)
            layout.setContentsMargins(0,0,0,0)
            widget.setLayout(layout)
            
            self.tableWidget.setCellWidget(i, column, widget)
            column += 1
            
            # Action
            pendingAction = revision['action']
            
            path = ""
            if( pendingAction == "edit" ):
                path = iconPath + "icon_blue.png"
            elif( pendingAction == "add" ):
                path = iconPath + "icon_green.png"
            elif( pendingAction == "delete" ):
                path = iconPath + "icon_red.png"

            widget = QtGui.QWidget()

            icon = QtGui.QPixmap(path)
            icon = icon.scaled(16, 16)
            
            iconLabel = QtGui.QLabel()
            iconLabel.setPixmap(icon)
            textLabel = QtGui.QLabel( pendingAction.capitalize() )
            textLabel.setStyleSheet( "QLabel { border: none } " )
            
            layout = QtGui.QHBoxLayout()
            layout.addWidget( iconLabel )
            layout.addWidget( textLabel )
            layout.setAlignment(QtCore.Qt.AlignLeft)
            #layout.setContentsMargins(0,0,0,0)
            widget.setLayout(layout)
            
            self.tableWidget.setCellWidget(i, column, widget)
            column += 1
            
            # Date
            date = revision['date']
            
            widget = QtGui.QWidget()
            layout = QtGui.QHBoxLayout()
            label = QtGui.QLabel(str(date))
            label.setStyleSheet( "QLabel { border: none } " )
            
            layout.addWidget( label )
            layout.setAlignment(QtCore.Qt.AlignCenter)
            layout.setContentsMargins( 4, 0, 4, 0)
            widget.setLayout(layout)
            
            self.tableWidget.setCellWidget(i, column, widget)
            column += 1
            
            
            # Description
            desc = revision['desc']
            
            widget = QtGui.QWidget()
            layout = QtGui.QHBoxLayout()
            text = QtGui.QLineEdit()
            text.setText( desc )
            text.setReadOnly(True)
            text.setAlignment( QtCore.Qt.AlignLeft )
            text.setStyleSheet( "QLineEdit { border: none " )
            
            layout.addWidget( text )
            layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignLeft)
            layout.setContentsMargins(4, 0, 1, 0)
            widget.setLayout(layout)
            
            self.tableWidget.setCellWidget(i, column, widget)
            column += 1
        
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.horizontalHeader().setStretchLastSection(True)


     
if __name__ == "arse":

    """ ------------- SUBMIT GUI ------------------ """
    
    #print p4.run_edit("TestFile.txt") 
    # ERRORS TO CHECK FOR (if the list doesn't contain a dictionary)
    # can't add existing file
    #
    
        # Make sure the UI is deleted before recreating
    try:
        submit_ui.deleteLater()
    except:
        pass
    
    # Create minimal UI object
    submit_ui = SubmitChangeUi()
    
    # Delete the UI if errors occur to avoid causing winEvent
    # and event errors (in Maya 2014)
    try:       
        files = p4.run_opened("...", "-a")
        #for file in files:
            #print file['depotFile']

        entries = []
        for file in files:
            filePath = file['depotFile']
            fileInfo = p4.run_fstat( filePath )[0]

            entry = {'File' : filePath, 
                     'Folder' : os.path.split(filePath)[0],
                     'Type' : fileInfo['type'],
                     'Pending_Action' : fileInfo['action'],
                     }

            entries.append(entry)

        submit_ui.create( entries )
        submit_ui.show()
    except:
        submit_ui.deleteLater()
        traceback.print_exc()
    
    """ FILE HISTORY GUI """
    
    

""" old stuff """
#lists = queryChangelists("pending")
#forceChangelistDelete(lists)

#editFiles = ["TestFile.txt", "TestFile2.txt"]
#addFiles = ["TestFile5.txt"]

#p4.run_edit( ["TestFile.txt", "TestFile2.txt"] )
#p4.run_add( ["fam.jpg"] )
#p4.run_delete("TestFile2.txt")

#files = editFiles + addFiles

#change = p4.fetch_change()
#change._description = "test p4python linux"
#print change._files

#for file in change._files:
#    print file, p4.run_opened(file)[0]['action']

#a = p4.run_opened( "//depot/TestFile.txt" )
#for x in a:
#    print x['depotFile']

#for x in change:
#    print x + ":" + str(change[x])

#p4.run_submit(change)


def submitChange(files, description, keepCheckedOut = False):
    change = p4.fetch_change()

    change._description = description    
    
    logging.info("Files Passed for submission = {0}".format(files))
    
    fileList = []
    changeFiles = [ entry['depotFile'] for entry in p4.run_opened() ]# change._files
    logging.info("Changelist = {0}".format(changeFiles))
    for changeFile in changeFiles :
        if changeFile in files:
            fileList.append(changeFile)
        else:
            logging.warning("File {0} ({1}) not in changelist".format(changeFile, p4.run_opened(changeFile)[0]['action']))
            
    logging.info("Final changelist files = {0}".format(fileList)) 
    change._files = fileList
    try:
        if keepCheckedOut:
            result = p4.run_submit(change, "-r")
        else:
            result = p4.run_submit(change)
        logging.info(result)
    except P4Exception as e:
        logging.warning(e)
        raise e

#fileDialog = QtGui.QFileDialog( maya_main_window(), "Add file(s)", str(p4.cwd) )
#fileDialog.directoryEntered.connect( onEnter )
#fileDialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
#fileDialog.show()
#files = fileDialog.selectedFiles()

#validFiles = []
#for file in files:
#    if isPathInClientRoot(file):
#        validFiles.append(file)

def syncPreviousRevision(file, revision, description):
    p4.run_sync("-f", "{0}#{1}".format(file, revision))

    change = p4.fetch_change()
    change._description = description

    result = p4.save_change(change)
    r = re.compile("Change ([1-9][0-9]*) created.")
    m = r.match(result[0])
    changeId = "0"
    if m:
        changeId = m.group(1)

    try:
        errors = []
        
        try:
            p4.run_edit("-c", changeId, file)
        except P4Exception as e:
            errors.append(e)
            
        try:
            p4.run_sync("-f", file)
        except P4Exception as e:
            errors.append(e)
        
        try:
            p4.run_resolve("-ay")
        except P4Exception as e:
            errors.append(e)

        try:
            change = p4.fetch_change(changeId)
        except P4Exception as e:
            errors.append(e)
            
        try:
            p4.run_submit(change)
        except P4Exception as e:
            errors.append(e)
        
        if errors:
            raise tuple(errors)
    except P4Exception as e:
        displayErrorUI(e)
        return False
    return True

def inDirectory(file, directory):
    #make both absolute    
    directory = os.path.join(os.path.realpath(directory), '')
    file = os.path.realpath(file)

    #return true, if the common prefix of both is equal to directory
    #e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return (os.path.commonprefix([file, directory]) == directory) or (os.path.abspath(file) == os.path.abspath(directory))




def isPathInClientRoot(path):
    if inDirectory(path, p4.cwd):
        return True
    else:
        logging.warning("{0} not in client root".format(path))
        return False




# Open files
#p4.run_opened("...")

# Close files
#p4.run_revert("...")



#results = queryChangelists("pending")
#for list in results:
#    print list

#forceChangelistDelete([ results[0] ])
#p4.run_change("45")

#p4.run_revert("FileTest5.txt")


def queryChangelists( status = None):
    if not status:
        args = ["changes"]
    else:
        args = ["changes", "-s", status]

    try:
        return p4.run(args)
    except P4Exception as e:
        logging.warning(e)
        raise e

def forceChangelistDelete(lists):
    for list in lists:
        try:
            isUser = (list['user'] == p4.user) 
            isClient = (list['client'] == p4.client)
            
            if isUser and isClient:
                logging.info("Deleting change {0} on client {1}".format(list['change'], list['client']))
                print list['change']
                p4.run_unlock("-c", list['change'])
                p4.run_revert("-c", list['change'], "...")
                p4.run_change("-d", list['change'])
            if not isUser:
                logging.warning( "User {0} doesn't own change {1}, can't delete".format(p4.user, list['change']) )
            if not isClient:
                logging.warning( "Client {0} doesn't own change {1}, can't delete".format(p4.client, list['change']) )
        except P4Exception as e:
            logging.critical(e)
            



import maya.cmds as cmds
import maya.mel
import maya.utils as mu

class PerforceUI:
    def __init__(self, p4):
        self.deleteUI = None
        self.submitUI = None
        self.perforceMenu = ""
        
        self.p4 = p4
        self.p4.connect()
        self.p4.run_login("-a")
        self.p4.cwd = p4.fetch_client()['Root']

        
    def addMenu(self):
        try:
            cmds.deleteUI(self.perforceMenu)
        except:
            pass
        
        gMainWindow = maya.mel.eval('$temp1=$gMainWindow')
        self.perforceMenu = cmds.menu(parent = gMainWindow, tearOff = True, label = 'Perforce')
        
        cmds.setParent(self.perforceMenu, menu=True)
        cmds.menuItem(label = "Basics", divider=True)
        cmds.menuItem(label="Checkout File",                     command = self.checkoutFile )
        cmds.menuItem(label="Delete File",                  command = self.deleteFile               )
        cmds.menuItem(label="Revert File",                  command = self.revertFile               )
        
        cmds.menuItem(label = "Changes", divider=True)
        cmds.menuItem(label="Submit Change",                command = self.submitChange             )
        cmds.menuItem(label="Opened Files",                 command = self.queryOpened              )
        
        cmds.menuItem(label = "Permissions", divider=True)
        self.lockFile = cmds.menuItem(label="Lock This File",               command = self.lockThisFile                 )
        self.unlockFile = cmds.menuItem(label="Unlock This File",             command = self.unlockThisFile, en=False     )
        cmds.menuItem(label="Lock File",                    command = self.lockFile                 )
        cmds.menuItem(label="Unlock File",                  command = self.unlockFile               )
        
        cmds.menuItem(label = "Revisions", divider=True)
        cmds.menuItem(label="Get Latest File",              command = self.syncFile                 )
        cmds.menuItem(label="Sync All",                     command = self.syncAll                  )
        cmds.menuItem(label="Sync All References",          command = self.syncAll, en=False        )
        cmds.menuItem(label="All File Revisions",           command = self.fileRevisions        )
        
        cmds.menuItem(label = "Scene", divider=True)
        cmds.menuItem(label="File Status",                  command = self.querySceneStatus       )
        
        cmds.menuItem(divider=True)
        cmds.menuItem(subMenu=True, tearOff=True, label="Preferences")
        cmds.menuItem(label="Auto-lock on add/edit?",       checkBox = True)
        cmds.menuItem(label="Login",                        command = "print(`Login`)"              )
        cmds.menuItem(label="Change Password",              command = "print(`Change password`)"    )
        cmds.menuItem(label="Server Info",                  command = "print(`Server Info`)"        )
        cmds.menuItem(label="Perforce Help",                command = "print(`Perforce Help`)"      )
        

    # Open up a sandboxed QFileDialog and run a command on all the selected files (and log the output)
    def __processClientFile(self, title, p4command, *p4args):
        fileDialog = QtGui.QFileDialog( maya_main_window(), title, str(self.p4.cwd) )
        
        def onEnter(*args):
            if not isPathInClientRoot(args[0]):
                fileDialog.setDirectory( p4.cwd )
                
        def onComplete(*args):
            # Only add files if we didn't cancel
            if args[0] == 1:
                for file in fileDialog.selectedFiles():
                    if isPathInClientRoot(file):
                        try: 
                            logging.info( p4command(p4args, file) )
                        except P4Exception as e:
                            logging.warning(e)
                    else:
                        logging.warning("{0} is not in client root.".format(file))
                
            fileDialog.deleteLater()
        
        
        fileDialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
        fileDialog.directoryEntered.connect( onEnter )
        fileDialog.finished.connect( onComplete )
        fileDialog.show()

    def checkoutFile(self, *args):
        self.__processClientFile("Checkout file(s)", self.run_checkoutFile)
        
    def run_checkoutFile(self, *args):
        for file in args[1:]:
            result = None
            try:
                result = self.p4.run_fstat(file)
            except P4Exception as e:
                pass
                
            try:
                if result:
                    logging.info(self.p4.run_edit(file))
                else:
                    logging.info(self.p4.run_add(file))
            except P4Exception as e:
                displayErrorUI(e)
                
        
    def deleteFile(self, *args):
        self.__processClientFile("Delete file(s)", self.p4.run_delete)
        
    def revertFile(self, *args):
        self.__processClientFile("Revert file(s)", self.p4.run_revert, "-k")     
        
    def lockFile(self, *args):
        self.__processClientFile("Lock file(s)", self.p4.run_lock)
        
    def unlockFile(self, *args):
        self.__processClientFile("Unlock file(s)", self.p4.run_unlock)
        
    def lockThisFile(self, *args):
        file =  getCurrentSceneFile()
        
        if not file:
            logging.warning("Current scene has no name")
            return
            
        if not isPathInClientRoot(file):
            logging.warning("{0} is not in client root".format(file))
            return
            
        try:
            p4.run_lock(file)
            logging.info("Locked file {0}".format(file))
            cmds.menuItem(self.unlockFile, edit=True, en=True)
            cmds.menuItem(self.lockFile, edit=True, en=False)
        except P4Exception as e:
            displayErrorUI(e)
        
    def unlockThisFile(self, *args):
        file =  getCurrentSceneFile()
        
        if not file:
            logging.warning("Current scene has no name")
            return
            
        if not isPathInClientRoot(file):
            logging.warning("{0} is not in client root".format(file))
            return
        
        try:
            p4.run_unlock( file )
            logging.info("Unlocked file {0}".format(file))
            cmds.menuItem(self.unlockFile, edit=True, en=False)
            cmds.menuItem(self.lockFile, edit=True, en=True)
        except P4Exception as e:
            displayErrorUI(e)
        
    def syncFile(self, *args):
        self.__processClientFile("Sync file(s)", self.p4.run_sync)

    def querySceneStatus(self, *args):
        try:
            result = p4.run_fstat("-Oa", getCurrentSceneFile())[0]
            text = ""
            for x in result:
                text += ("{0} : {1}\n".format(x, result[x]))
            QtGui.QMessageBox.information(mainParent, "Scene Info", text)
        except P4Exception as e:
            displayErrorUI(e)
        
        
    def fileRevisions(self, *args):
        try:
            self.revisionUi.deleteLater()
        except:
            pass

        self.revisionUi = FileRevisionUI()

        # Delete the UI if errors occur to avoid causing winEvent
        # and event errors (in Maya 2014)
        try:       
            self.revisionUi.create()
            self.revisionUi.show()
        except:
            self.revisionUi.deleteLater()
            traceback.print_exc()

    def queryOpened(self, *args):
        try:
            self.openedUI.deleteLater()
        except:
            pass

        self.openedUI = OpenedFilesUI()

        # Delete the UI if errors occur to avoid causing winEvent
        # and event errors (in Maya 2014)
        try:       
            files = p4.run_opened("...", "-a")

            entries = []
            for file in files:
                filePath = file['depotFile']
                fileInfo = p4.run_fstat( filePath )[0]

                entry = {'File' : filePath, 
                         'Folder' : os.path.split(filePath)[0],
                         'Type' : fileInfo['type'],
                         'Pending_Action' : fileInfo['action'],
                         }

                entries.append(entry)

            self.openedUI.create( entries )
            self.openedUI.show()
        except:
            self.openedUI.deleteLater()
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
            files = p4.run_opened("...", "-a")

            entries = []
            for file in files:
                filePath = file['depotFile']
                fileInfo = p4.run_fstat( filePath )[0]

                entry = {'File' : filePath, 
                         'Folder' : os.path.split(filePath)[0],
                         'Type' : fileInfo['type'],
                         'Pending_Action' : fileInfo['action'],
                         }

                entries.append(entry)

            self.submitUI.create( entries )
            self.submitUI.show()
        except:
            self.submitUI.deleteLater()
            traceback.print_exc()
        
    def syncFile(self, *args):
        try:
            p4.run_sync("-f", getCurrentSceneFile())
            logging.info("Got latest revision for {0}".format(getCurrentSceneFile()))
        except P4Exception as e:
            displayErrorUI(e)
        
    def syncAll(self, *args):
        try:
            p4.run_sync("-f", "...")
            logging.info("Got latest revisions for client")
        except P4Exception as e:
            displayErrorUI(e)
        
    def fileHistory(self, *args):
        print "File History",
        print args
        
    def fileStatus(self, *args):
        print "File Status"
        print args
      
if __name__ == "__main__":
    try:
        cmds.deleteUI(ui.perforceMenu)
    except:
        pass

    PORT = "ssl:52.17.163.3:1666"
    USER = "tminor"
    p4 = P4()
    p4.port = PORT
    p4.user = USER
    p4.password = "contact_dev"

    ui = PerforceUI(p4)
    ui.addMenu()

    #mu.executeDeferred('ui.addMenu()')

