import traceback
import os

from PySide import QtCore
from PySide import QtGui
import logging

from P4 import P4, P4Exception

from shiboken import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

# Hacky way to load our icons, I don't fancy wrestling with resource files
iconPath = os.environ['MAYA_APP_DIR'] + "/scripts/images/"
tempPath = os.environ['TMPDIR']

PORT = "ssl:52.17.163.3:1666"
USER = "tminor"
p4 = P4()
p4.port = PORT
p4.user = USER
p4.password = "contact_dev"
p4.connect()
p4.run_login("-a")

p4.cwd = p4.fetch_client()['Root']

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)
        

class SubmitChangeUi(QtGui.QDialog):
    def __init__(self, parent=maya_main_window()):
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
        if not self.validateText:
            cmds.confirmDialog(title="Warning", message = "Empty description")
        
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
            error_ui = QtGui.QMessageBox()
            error_ui.setWindowFlags(QtCore.Qt.WA_DeleteOnClose)
            
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
            
            if "[Warning]" in str(e):
                eMsg = eMsg.replace("[Warning]:", "")
                error_ui.warning(maya_main_window(), "Submit Warning", eMsg)
            elif "[Error]" in str(e):
                eMsg = eMsg.replace("[Error]:", "")
                error_ui.critical(maya_main_window(), "Submit Error", eMsg)
            error_ui.deleteLater()               

    def validateText(self):
        text = self.descriptionWidget.toPlainText()
        p = QtGui.QPalette()
        if text == "<Enter Description>" or "<" in text or ">" in text:
            p.setColor(QtGui.QPalette.Active,   QtGui.QPalette.Text, QtCore.Qt.red)
            p.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Text, QtCore.Qt.red)
        self.descriptionWidget.setPalette(p) 
        
    def on_text_changed(self):
        self.validateText()

     
     
if __name__ == "__main__":

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

        print entries

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
#fileDialog.show()

def isPathInClientRoot(path):
    try:
        if os.path.isdir(path):
            p4.run_files(os.path.join(path, "..."))
        else:
            p4.run_files(path)
        return True
    except P4Exception as e:
        logging.warning(e)
        return False

def onEnter(*args):
    if not isPathInClientRoot(args[0]):
        fileDialog.setDirectory( p4.cwd )


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