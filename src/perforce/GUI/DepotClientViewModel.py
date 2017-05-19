import os

from P4 import P4, P4Exception
from Qt import QtCore, QtGui, QtWidgets

import perforce.Utils as Utils
from perforce.AppInterop import interop

def epochToTimeStr(time):
    import datetime
    return datetime.datetime.utcfromtimestamp(int(time)).strftime("%d/%m/%Y %H:%M:%S")

def perforceIsDir(p4path):
    try: 
        if p4path[-1] in ['/', '\\']:
            p4path = p4path[:-1]

        result = p4.run_dirs(p4path)
        return len(result) > 0
    except P4Exception as e:
        print e
        return False

def fullPath(idx):
    result = [idx]

    parent = idx.parent()
    while True:
        if not parent.isValid():
            break
        result.append(parent)
        parent = parent.parent()

    return list(reversed(result))

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

class PerforceItemModel(QtCore.QAbstractItemModel):

    def __init__(self, p4, parent=None):
        super(PerforceItemModel, self).__init__(parent)

        self.p4 = p4
        self.rootItem = PerforceItem(None)
        self.showDeleted = False

    

    def perforceListDir(self, p4path):
        result = []

        if p4path[-1] == '/' or p4path[-1] == '\\':
            p4path = p4path[:-1]

        path = "{0}/{1}".format(p4path, '*')

        isDepotPath = p4path.startswith("//depot")


        dirs = []
        with self.p4.at_exception_level(P4.RAISE_ERRORS):
            dirs = self.p4.run_dirs(path)

        files = []
        with self.p4.at_exception_level(P4.RAISE_ERRORS):
            if isDepotPath:
                files = self.p4.run_files(path)
            else:
                tmp = self.p4.run_have(path)
                for fileItem in tmp:
                    files += self.p4.run_fstat(fileItem['clientFile'])

        result = []

        for dir in dirs:
            if isDepotPath:
                dirName = dir['dir'][8:]
            else:
                dirName = dir['dir']

            tmp = {'name': os.path.basename(dirName),
                   'path': dir['dir'],
                   'time': '',
                   'type': 'Folder',
                   'change': ''
                   }
            result.append(tmp)

        for fileItem in files:
            if isDepotPath:
                deleteTest = self.p4.run("filelog", "-t", fileItem['depotFile'])[0]
                isDeleted = deleteTest['action'][0] == "delete"
                fileType = fileItem['type']
                if isDeleted:
                    fileType = "{0} [Deleted]".format(fileType)
                # Remove //depot/ from the path for the 'pretty' name
                tmp = {'name': os.path.basename(fileItem['depotFile'][8:]),
                       'path': fileItem['depotFile'],
                       'time': epochToTimeStr(fileItem['time']),
                       'type': fileType,
                       'change': fileItem['change']
                       }
                result.append(tmp)
            else:
                deleteTest = self.p4.run("filelog", "-t", fileItem['clientFile'])[0]
                isDeleted = deleteTest['action'][0] == "delete"
                fileType = fileItem['headType']
                if isDeleted:
                    fileType = "{0} [Deleted]".format(fileType)
                tmp = {'name': os.path.basename(fileItem['clientFile']),
                       'path': fileItem['clientFile'],
                       'time': epochToTimeStr(fileItem['headModTime']),
                       'type': fileType,
                       'change': fileItem['headChange']
                       }
                result.append(tmp)

        return sorted(result, key=lambda k: k['name'])

    

    def populate(self, rootdir, showDeleted=False):
        self.rootItem = PerforceItem(None)
        self.showDeleted = showDeleted

        self.populateSubDir()

    def populateSubDir(self, idx=None, root="//depot", showDeleted=False):
        # Overcomplicated way to figure out if idx is root or not
        # Would be better to check if .parent() and if not return the root path
        if idx:
            idxPathModel = fullPath(idx)
            idxPathSubDirs = [idxPath.data() for idxPath in idxPathModel]
            idxFullPath = '/'.join(idxPathSubDirs)

            if not idxFullPath:
                idxFullPath = "."

            p4path = '/'.join([root, idxFullPath])

            treeItem = idx.internalPointer()

            # Pop empty "None" child
            treeItem.popChild()
        else:
            p4path = '/'.join([root])

            treeItem = self.rootItem

        isDepotPath = root.startswith("//depot")

        dirpath = '/'.join([p4path,'*'])

        with self.p4.at_exception_level(P4.RAISE_ERRORS):
            args = [dirpath]
            if isDepotPath:
                args.insert(0, '-H')
            p4subdirs = [childDir['dir'] for childDir in self.p4.run_dirs(*args)]

            # Add the sub directories first
            Utils.p4Logger().debug('p4.run_dirs(%s) =' % (p4path) )
            for childDir in p4subdirs:
                Utils.p4Logger().debug('\t%s' % childDir )
                treeItem.appendFolderItem(childDir)


            p4subfiles = self.p4Filelist(dirpath)
            Utils.p4Logger().debug('p4FileList(%s) = ' % dirpath)
            for f in p4subfiles:
                Utils.p4Logger().debug('\t%s' % f)
                treeItem.appendFileItem( f['name'], f['type'], f['time'], f['action'], f['change'] )

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