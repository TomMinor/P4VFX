import platform
import traceback
import os
import re

from P4 import P4, P4Exception

import perforce.Utils as Utils
from perforce.DCCInterop import interop

from Qt import QtCore, QtGui, QtWidgets

class MainShelf:

    def __init__(self, p4):
        self.deleteUI = None
        self.submitUI = None
        # self.perforceMenu = ""

        self.p4 = p4
        self.p4.connect()

        try:
            self.firstTimeLogin(enterUsername=self.p4.user is None,
                                enterPassword=self.p4.password is None)
        except P4Exception as e:
            # If user/pass is set but it fails anyway, try a last ditch attempt
            # to let the user input their stuff
            try:
                self.firstTimeLogin(enterUsername=self.p4.user is None,
                                    enterPassword=True)
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
                Utils.p4Logger().warning(e)

        self.p4.cwd = self.p4.fetch_client()['Root']

    def close(self):
        try:
            self.revisionUi.deleteLater()
        except Exception as e:
            print "Error cleaning up P4 revision UI : ", e

        try:
            self.openedUi.deleteLater()
        except Exception as e:
            print "Error cleaning up P4 opened UI : ", e

        # try:
        #     # Deleting maya menus is bad, but this is a dumb way of error checking
        #     if "PerforceMenu" in self.perforceMenu:
        #         AppUtils.closeWindow(self.perforceMenu)
        #     else:
        #         raise RuntimeError("Menu name doesn't seem to belong to Perforce, not deleting")
        # except Exception  as e:
        #     print "Error cleaning up P4 menu : ", e

        try:
            self.submitUI.deleteLater()
        except Exception as e:
            print "Error cleaning up P4 submit UI : ", e

        Utils.p4Logger().info("Disconnecting from server")
        try:
            self.p4.disconnect()
        except Exception as e:
            print "Error disconnecting P4 daemon : ", e

    def addMenu(self):
        try:
            interop.closeWindow(self.perforceMenu)
        except:
            pass

        # %TODO Hard coded icons are bad?
        iconPath = interop.getIconPath()

        menuEntries = [
            {'label': "Client Commands",            'divider': True},
            {'label': "Checkout File(s)",           'image': os.path.join(
                iconPath, "File0078.png"), 'command': self.checkoutFile},
            {'label': "Checkout Folder",            'image': os.path.join(
                iconPath, "File0186.png"), 'command': self.checkoutFolder},
            {'label': "Mark for Delete",            'image': os.path.join(
                iconPath, "File0253.png"), 'command': self.deleteFile},
            {'label': "Show Changelist",            'image': os.path.join(
                iconPath, "File0252.png"), 'command': self.queryOpened},
            {'label': "Depot Commands",             'divider': True},
            {'label': "Submit Change",              'image': os.path.join(
                iconPath, "File0107.png"), 'command': self.submitChange},
            {'label': "Sync All",                   'image': os.path.join(
                iconPath, "File0175.png"), 'command': self.syncAllChanged},
            {'label': "Sync All - Force",
                'image': os.path.join(iconPath, "File0175.png"), 'command': self.syncAll},
            # {'label': "Sync All References",        'image': os.path.join(iconPath, "File0320.png"), 'command': self.syncAllChanged},
            #{'label': "Get Latest Scene",          'image': os.path.join(iconPath, "File0275.png"), command = self.syncFile},
            {'label': "Show Depot History",         'image': os.path.join(
                iconPath, "File0279.png"), 'command': self.fileRevisions},

            {'label': "Scene",                      'divider': True},
            {'label': "File Status",                'image': os.path.join(
                iconPath, "File0409.png"), 'command': self.querySceneStatus},

            {'label': "Utility",                    'divider': True},
            {'label': "Create Asset",               'image': os.path.join(
                iconPath, "File0352.png"), 'command': self.createAsset},
            {'label': "Create Shot",                'image': os.path.join(
                iconPath, "File0104.png"), 'command': self.createShot},
            # Submenu
            {
                'label': "Miscellaneous",           'image': os.path.join(iconPath, "File0411.png"), 'entries': [
                    {'label': "Server",                     'divider': True},
                    {'label': "Login as user",              'image': os.path.join(
                        iconPath, "File0077.png"),    'command': self.loginAsUser},
                    {'label': "Server Info",                'image': os.path.join(
                        iconPath, "File0031.png"),    'command': self.queryServerStatus},
                    {'label': "Workspace",                  'divider': True},
                    {'label': "Create Workspace",           'image': os.path.join(
                        iconPath, "File0238.png"),    'command': self.createWorkspace},
                    {'label': "Set Current Workspace",      'image': os.path.join(
                        iconPath, "File0044.png"),    'command': self.setCurrentWorkspace},
                    {'label': "Debug",                      'divider': True},
                    {'label': "Delete all pending changes", 'image': os.path.join(
                        iconPath, "File0280.png"),    'command': self.deletePending}
                ]
            }
        ]

        interop.createMenu(menuEntries)

    def changePasswd(self, *args):
        return NotImplementedError("Use p4 passwd")

    def createShot(self, *args):
        shotNameDialog = QtGui.QInputDialog
        shotName = shotNameDialog.getText(
            interop.main_parent_window(), "Create Shot", "Shot Name:")

        if not shotName[1]:
            return

        if not shotName[0]:
            Utils.p4Logger().warning("Empty shot name")
            return

        shotNumDialog = QtGui.QInputDialog
        shotNum = shotNumDialog.getText(
            interop.main_parent_window(), "Create Shot", "Shot Number:")

        if not shotNum[1]:
            return

        if not shotNum[0]:
            Utils.p4Logger().warning("Empty shot number")
            return

        shotNumberInt = -1
        try:
            shotNumberInt = int(shotNum[0])
        except ValueError as e:
            Utils.p4Logger().warning(e)
            return

        Utils.p4Logger().info("Creating folder structure for shot {0}/{1} in {2}".format(
            shotName[0], shotNumberInt, self.p4.cwd))
        dir = Utils.createShotFolders(self.p4.cwd, shotName[0], shotNumberInt)
        self.run_checkoutFolder(None, dir)

    def createAsset(self, *args):
        assetNameDialog = QtGui.QInputDialog
        assetName = assetNameDialog.getText(
            interop.main_parent_window(), "Create Asset", "Asset Name:")

        if not assetName[1]:
            return

        if not assetName[0]:
            Utils.p4Logger().warning("Empty asset name")
            return

        Utils.p4Logger().info("Creating folder structure for asset {0} in {1}".format(
            assetName[0], self.p4.cwd))
        dir = Utils.createAssetFolders(self.p4.cwd, assetName[0])
        self.run_checkoutFolder(None, dir)

    def loginAsUser(self, *args):
        self.firstTimeLogin(enterUsername=True, enterPassword=True)

    def firstTimeLogin(self, enterUsername=True, enterPassword=True, *args):
        username = None
        password = None

        print interop.main_parent_window()

        if enterUsername:
            username, ok = QtWidgets.QInputDialog.getText(
                interop.main_parent_window(),
                "Enter username",
                "Username:",
                QtWidgets.QLineEdit.Normal
                )

            if not username or not ok:
                raise ValueError("Invalid username")

            self.p4.user = str(username)

        if enterPassword:
            password, ok = QtWidgets.QInputDialog.getText(
                interop.main_parent_window(),
                "Enter password",
                "Password:",
                QtWidgets.QLineEdit.Password)

            if not password or not ok:
                raise ValueError("Invalid password")

            self.p4.password = str(password)

        # Validate SSH Login / Attempt to login
        try:
            Utils.p4Logger().info(self.p4.run_login("-a"))
        except P4Exception as e:
            regexKey = re.compile(ur'(?:[0-9a-fA-F]:?){40}')
            # regexIP = re.compile(ur'[0-9]+(?:\.[0-9]+){3}?:[0-9]{4}')
            errorMsg = str(e).replace('\\n', ' ')

            key = re.findall(regexKey, errorMsg)
            # ip = re.findall(regexIP, errorMsg)

            if key:
                Utils.p4Logger().info(self.p4.run_trust("-i", key[0]))
                Utils.p4Logger().info(self.p4.run_login("-a"))
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
            interop.main_parent_window(), "Select existing workspace")

        for client in self.p4.run_clients():
            if workspacePath.replace("\\", "/") == client['Root'].replace("\\", "/"):
                root, client = os.path.split(str(workspacePath))
                self.p4.client = client

                Utils.p4Logger().info(
                    "Setting current client to {0}".format(client))
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
                interop.main_parent_window(), "Perforce Error", "{0} is not a workspace root".format(workspacePath))

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
                interop.main_parent_window(), "Workspace", "Optional Name Suffix (e.g. Uni, Home):")

            Utils.createWorkspace(self.p4, workspaceRoot,
                                  str(workspaceSuffix[0]))
            Utils.writeToP4Config(self.p4.p4config_file,
                                  "P4CLIENT", self.p4.client)
        except P4Exception as e:
            displayErrorUI(e)

    # Open up a sandboxed QFileDialog and run a command on all the selected
    # files (and log the output)
    def __processClientFile(self, title, finishCallback, preCallback, p4command, *p4args):
        fileDialog = QtGui.QFileDialog(interop.main_parent_window(), title, str(self.p4.cwd))

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
                            Utils.p4Logger().info(p4command(p4args, file))
                            selectedFiles.append(file)
                        except P4Exception as e:
                            Utils.p4Logger().warning(e)
                            error = e
                    else:
                        Utils.p4Logger().warning(
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
        fileDialog = QtGui.QFileDialog(interop.main_parent_window(), title, str(self.p4.cwd))

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
                            Utils.p4Logger().info(p4command(p4args, file))
                            selectedFiles.append(file)
                        except P4Exception as e:
                            Utils.p4Logger().warning(e)
                            error = e
                    else:
                        Utils.p4Logger().warning(
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
                            interop.main_parent_window(), "Open Scene?", "Do you want to open the checked out scene?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
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
            Utils.p4Logger().info("Processing {0}...".format(file))
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
                        Utils.p4Logger().info(self.p4.run_edit(file))
                        Utils.p4Logger().info(self.p4.run_lock(file))
                else:
                    Utils.p4Logger().info(self.p4.run_add(file))
                    Utils.p4Logger().info(self.p4.run_lock(file))
            except P4Exception as e:
                displayErrorUI(e)

    def deleteFile(self, *args):
        self.__processClientFile(
            "Delete file(s)", None, lambda x: Utils.addReadOnlyBit(x), self.p4.run_delete)

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
        #     Utils.p4Logger().warning("Current scene has no name")
        #     return

        # if not Utils.isPathInClientRoot(self.p4, file):
        #     Utils.p4Logger().warning("{0} is not in client root".format(file))
        #     return

        # try:
        #     self.p4.run_lock(file)
        #     Utils.p4Logger().info("Locked file {0}".format(file))

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
        #     Utils.p4Logger().warning("Current scene has no name")
        #     return

        # if not Utils.isPathInClientRoot(self.p4, file):
        #     Utils.p4Logger().warning("{0} is not in client root".format(file))
        #     return

        # try:
        #     self.p4.run_unlock( file )
        #     Utils.p4Logger().info("Unlocked file {0}".format(file))

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
                Utils.p4Logger().warning("Current scene file isn't saved.")
                return

            result = self.p4.run_fstat("-Oa", scene)[0]
            text = ""
            for x in result:
                text += ("{0} : {1}\n".format(x, result[x]))
            QtGui.QMessageBox.information(interop.main_parent_window(), "Scene Info", text)
        except P4Exception as e:
            displayErrorUI(e)

    def queryServerStatus(self, *args):
        try:
            result = self.p4.run_info()[0]
            text = ""
            for x in result:
                text += ("{0} : {1}\n".format(x, result[x]))
            QtGui.QMessageBox.information(interop.main_parent_window(), "Server Info", text)
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
            Utils.p4Logger().info("Got latest revision for {0}".format(
                AppUtils.getCurrentSceneFile()))
        except P4Exception as e:
            displayErrorUI(e)

    def syncAll(self, *args):
        try:
            self.p4.run_sync("-f", "...")
            Utils.p4Logger().info("Got latest revisions for client")
        except P4Exception as e:
            displayErrorUI(e)

    def syncAllChanged(self, *args):
        try:
            self.p4.run_sync("...")
            Utils.p4Logger().info("Got latest revisions for client")
        except P4Exception as e:
            displayErrorUI(e)
