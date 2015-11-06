###############################################################################
# Name: 
#   test_ui.py
#
# Description: 
#   PySide example that demonstrates using signals and slots
#
# Author: 
#   Chris Zurbrigg (http://zurbrigg.com)
#
###############################################################################

import traceback
import os

from PySide import QtCore
from PySide import QtGui

from shiboken import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

# Hacky way to load our icons, I don't fancy wrestling with resource files
iconPath = os.environ['MAYA_APP_DIR'] + "/scripts/images/"
tempPath = os.environ['TEMP']

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)
    
class ErrorUi(QtGui.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(ErrorUi, self).__init__(parent)
        
    def create(self, title, message):
        self.setWindowTitle(title)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setFixedSize(True)
        
        self.createControls()
        self.createLayout()
        self.createConnections()
        
    def createControls(self):
        self.confirmBtn = QtGui.QAbstractButton("Okay")
        self.label = QtGui.QLabel(message)
        
    def createLayout(self):
        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.confirmBtn)
        
        #main_layout.addStretch()
        
        self.setLayout(main_layout)
        
    def createConnections(self):
        pass
        

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
            self.tableWidget.setItem(i, column, newItem) 
            column += 1
            
            # Text
            fileType = file['Type']
            newItem = QtGui.QTableWidgetItem( fileType.capitalize() )
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
            self.tableWidget.setItem(i, column, newItem) 
            column += 1
        
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        #self.tableWidget.setColumnWidth(1, 120)
        #self.tableWidget.setColumnWidth(2, 180)
        #self.tableWidget.setColumnWidth(3, 60)
        
        
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
        submitChange(files, str(self.descriptionWidget.toPlainText()) )
                

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
    
    # Development workaround for PySide winEvent error (in Maya 2014)
    # Make sure the UI is deleted before recreating
    try:
        test_ui.deleteLater()
    except:
        pass
    
    # Create minimal UI object
    test_ui = SubmitChangeUi()
    
    # Delete the UI if errors occur to avoid causing winEvent
    # and event errors (in Maya 2014)
    try:
        p4.run_edit("...")
        p4.run_edit("TestFile.txt")
        p4.run_edit("TestFile2.txt")
        p4.run_edit("TestFile3.txt")
        p4.run_add("TestFile4.txt")
        p4.run_revert("TestFile3.txt")
        p4.run_delete("TestFile3.txt")

        files = p4.run_opened("...", "-a")
        for file in files:
            print file
        
        entries = []
        for file in files:
            fileInfo = p4.run_fstat( file['clientFile'] )[0]
            print fileInfo
            
            entries.append( {'File' : file['clientFile'], 
                             'Folder' : os.path.split(file['depotFile'])[0],
                             'Type' : fileInfo['type'],
                             'Pending_Action' : fileInfo['action'],
                             }
                            )
        
        test_ui.create( entries )
        test_ui.show()
    except:
        test_ui.deleteLater()
        traceback.print_exc()