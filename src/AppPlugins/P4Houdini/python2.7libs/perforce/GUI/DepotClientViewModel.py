import os

from P4 import P4, P4Exception
from qtpy import QtCore, QtGui, QtWidgets

import perforce.Utils as Utils
from perforce.AppInterop import interop

def epochToTimeStr(time):
    import datetime
    return datetime.datetime.utcfromtimestamp(int(time)).strftime("%d/%m/%Y %H:%M:%S")

class PerforceItem(object):

    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.data = data
        self.childItems = []

    def appendFileItem(self, filepath, filetype, time, action, change):
        fileName = os.path.basename(filepath)

        # Kludge to pass through the raw path as an extra column that simply isn't used
        data = (fileName, filetype, time, action, change, filepath)

        fileItem = PerforceItem(data, self)
        self.appendChild(fileItem)

    def appendFolderItem(self, dirpath):
        dirName = os.path.basename(dirpath)

        # Kludge to pass through the raw path as an extra column that simply isn't used
        data = (dirName, 'Folder', '', '', '', dirpath)

        fileItem = PerforceItem(data, self)
        self.appendChild(fileItem)
        fileItem.appendChild(None)


    def appendChild(self, item):
        self.childItems.append(item)

    def popChild(self):
        if self.childItems:
            self.childItems.pop()

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0

    @staticmethod
    def absoluteP4Path(idx):
        result = [idx]

        parent = idx.parent()
        while True:
            if not parent.isValid():
                break
            result.append(parent)
            parent = parent.parent()

        return list(reversed(result))

class PerforceItemModel(QtCore.QAbstractItemModel):
    def __init__(self, p4, parent=None):
        super(PerforceItemModel, self).__init__(parent)

        self.p4 = p4
        self.showDeleted = False
        self.rootItem = None

    def populate(self, rootdir):
        self.rootItem = PerforceItem(None)
        Utils.p4Logger().debug('Populating: %s' % rootdir)
        self.populateSubDir(idx=None, root=rootdir)

    def populateSubDir(self, idx=None, root="//depot"):
        # Overcomplicated way to figure out if idx is root or not
        # Would be better to check if .parent() exists and if not return the root path
        if idx:
            idxPathModel = PerforceItem.absoluteP4Path(idx)
            idxPathSubDirs = [idxPath.data() for idxPath in idxPathModel]
            idxFullPath = '/'.join(idxPathSubDirs)

            p4path = '/'.join([root, idxFullPath])
            treeItem = idx.internalPointer()

            # Pop empty "None" child
            treeItem.popChild()
        else:
            p4path = root
            treeItem = self.rootItem

        isDepotPath = root.startswith("//depot")
        isClientPath = not isDepotPath
        clientRoot = "//{0}".format(self.p4.client)

        # dirpath = '/'.join([p4path,'*'])

        with self.p4.at_exception_level(P4.RAISE_ERRORS):
            fstat_args = ['-Olhp', '-Dl', '/'.join([p4path,'*'])]
            # if not showDeleted:
            #     fstat_args.insert(1, '-F "^headAction=delete & ^headAction=move/delete"')
            p4fstat = self.p4.run_fstat(*fstat_args)

            files = []
            folders = []
            for f in p4fstat:
                # p4 fstat returns directory information as well
                if f.get('dir'):
                    folders.append(f)
                else:
                    files.append(f)

            for f in folders:
                # For some reason fstat gives us the depot path, we ~should~ be safe with a simple replace
                if isClientPath:
                    f['dir'] = f['dir'].replace('//depot', clientRoot)

                Utils.p4Logger().debug('Dir: \t%s' % f['dir'] )
                treeItem.appendFolderItem(f['dir'])
            
            for f in files:
                filepath = f['depotFile'] if isDepotPath else f['clientFile']
                Utils.p4Logger().debug('File: \t%s' % filepath)

                # Check if this is in a pending changelist,
                # which gives us different fields to query
                if f.get('change'):
                    if f['action'] in ['delete','move/delete'] and isClientPath:
                        continue

                    treeItem.appendFileItem( filepath, f['type'], '', f['action'], f['workRev'] )
                else:
                    # Only show deleted files in depot view (for the purpose of undeleting them)
                    if f['headAction'] in ['delete','move/delete'] and isClientPath:
                        continue

                    treeItem.appendFileItem( filepath, f['headType'], f['headTime'], f['headAction'], f['headRev'] )

            # Show pending changelist folders in client view
            # (fstat is configured to automatically add the files above if they exist in the current directory,
            # but if they exist in a subdir they won't be found by default)
            if isClientPath:
                # if not showDeleted:
                #     fstat_args.insert(1, '-F "^headAction=delete & ^headAction=move/delete"')

                # Query pending changes (just default for now)
                fstat_pending_args = ['-Or', '-F', 'change=default', '/'.join([p4path,'...'])]
                p4fstat = self.p4.run_fstat(*fstat_pending_args)
                if p4fstat:
                    p4fstat = p4fstat[0]
                    Utils.p4Logger().debug('fstat(%s): %s' % (fstat_pending_args, p4fstat['clientFile']))

                    workspaceRoot = os.path.normpath(self.p4.run_info()[0]['clientRoot'].replace('\\', '/'))
                    p4path = os.path.normpath(p4path).replace(workspaceRoot, '')
                    p4PendingPath = os.path.normpath(p4fstat['clientFile']).replace(workspaceRoot, '')

                    pendingPath, pendingFile = os.path.split(p4PendingPath)
                    pendingPathSplit = pendingPath.split(os.sep)
                    commonPrefixSplit = os.path.commonprefix([pendingPath, p4path]).split(os.sep)
                    uncommonDirectories = filter(lambda x: x not in commonPrefixSplit, pendingPathSplit) 

                    if uncommonDirectories:
                        currentDir = uncommonDirectories[0]
                        currentFolders = [ os.path.basename(f['dir']) for f in folders ]

                        Utils.p4Logger().debug( commonPrefixSplit )
                        Utils.p4Logger().debug( uncommonDirectories )
                        if not currentDir in currentFolders:
                            Utils.p4Logger().debug('Adding pending path folder')
                            treeItem.appendFolderItem( os.path.join(p4path, currentDir) )

        Utils.p4Logger().debug('\n\n')

    def p4Filelist(self, path):
        results = []
    
        # Query existing files in the depot/workspace
        with self.p4.at_exception_level(P4.RAISE_ERRORS):
            files = self.p4.run_filelog("-t", path)

            for x in files:
                latestRevision = x.revisions[0]

                if not self.showDeleted and latestRevision.action == 'delete':
                    continue
                else:
                    results.append({'name': latestRevision.depotFile,
                                    'action': latestRevision.action,
                                    'change': latestRevision.change,
                                    'time': str(latestRevision.time),
                                    'type': latestRevision.type
                                    }
                                   )

        # Query files only existing in pending changelists
        # and not added yet
        with self.p4.at_exception_level(P4.RAISE_ERRORS):
            filesInCurrentChange = self.p4.run_opened(path)
            for x in filesInCurrentChange:
                if x['action'] == 'add':
                    results.append({'name': x['clientFile'],
                                    'action': x['action'],
                                    'change': x['change'],
                                    'time': "",
                                    'type': x['type']
                                    }
                                   )

        return results

    def columnCount(self, parent):
        return 5

    def data(self, index, role):
        column = index.column()
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            item = index.internalPointer()
            return item.data[column]
        elif role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(20, 20)
        elif role == QtCore.Qt.DecorationRole:
            if column == 1:
                itemType = index.internalPointer().data[column]
                isDeleted = index.internalPointer().data[3] == 'delete'

                if isDeleted:
                    return QtGui.QIcon(os.path.join(interop.getIconPath(), 'File0104.png'))

                # Try to figure out which icon is most applicable to the item
                if itemType == "Folder":
                    return QtGui.QIcon(os.path.join(interop.getIconPath(), 'File0059.png'))
                elif "binary" in itemType:
                    return QtGui.QIcon(os.path.join(interop.getIconPath(), 'File0315.png'))
                elif "text" in itemType:
                    return QtGui.QIcon(os.path.join(interop.getIconPath(), 'File0027.png'))
                else:
                    return QtGui.QIcon(os.path.join(interop.getIconPath(), 'File0106.png'))
            else:
                return None

        return None

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ["Filename", "Type", "Modification Time", "Action", "Change"][section]
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.childItems[row]
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        parentItem = index.internalPointer().parentItem
        if parentItem == self.rootItem:
            return QtCore.QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rootrowcount(self):
        return len(self.rootItem.childItems)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        return len(parentItem.childItems)