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
        #  
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

def p4Filelist(p4, dir, findDeleted=False):
        p4path = '/'.join([dir, '*'])
        try:
            files = p4.run_filelog("-t", p4path)
        except P4Exception as e:
            # print e
            return []

        results = []

        for x in files:
            latestRevision = x.revisions[0]
            # print latestRevision.action, latestRevision.depotFile

            if not findDeleted and latestRevision.action == 'delete':
                continue
            else:
                results.append({'name': latestRevision.depotFile,
                                'action': latestRevision.action,
                                'change': latestRevision.change,
                                'time': latestRevision.time,
                                'type': latestRevision.type
                                }
                               )

        filesInCurrentChange = p4.run_opened(p4path)
        for x in filesInCurrentChange:
            # print x
            results.append({'name': x['clientFile'],
                            'action': x['action'],
                            'change': x['change'],
                            'time': "",
                            'type': x['type']
                            }
                           )

        return results

class TreeItem(object):

    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.data = data
        self.childItems = []

    def appendFileItem(self, filepath, filetype, time, action, change):
        fileName = os.path.basename(filepath)

        # Kludge to pass through the raw path as an extra column that simply isn't used
        data = (fileName, filetype, time, action, change, filepath)

        fileItem = TreeItem(data, self)
        self.appendChild(fileItem)

    def appendFolderItem(self, dirpath):
        dirName = os.path.basename(dirpath)

        # Kludge to pass through the raw path as an extra column that simply isn't used
        data = (dirName, 'Folder', '', '', '', dirpath)

        fileItem = TreeItem(data, self)
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

class TreeModel(QtCore.QAbstractItemModel):

    def __init__(self, p4, parent=None):
        super(TreeModel, self).__init__(parent)

        self.p4 = p4
        self.rootItem = TreeItem(None)
        self.showDeleted = False

    

    def perforceListDir(self, p4path):
        result = []

        if p4path[-1] == '/' or p4path[-1] == '\\':
            p4path = p4path[:-1]

        path = "{0}/{1}".format(p4path, '*')

        isDepotPath = p4path.startswith("//depot")

        dirs = []
        files = []

        # Dir silently does nothing if there are no dirs
        try:
            dirs = self.p4.run_dirs(path)
        except P4Exception:
            pass

        # Files will return an exception if there are no files in the dir
        # Stupid inconsistency imo
        try:
            if isDepotPath:
                files = self.p4.run_files(path)
            else:
                tmp = self.p4.run_have(path)
                for fileItem in tmp:
                    files += self.p4.run_fstat(fileItem['clientFile'])
        except P4Exception:
            pass

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

    

    def populate(self, rootdir, findDeleted=False):
        self.rootItem = TreeItem(None)
        self.showDeleted = findDeleted

        depotPath = "//depot" in rootdir

        p4path = '/'.join([rootdir, '*'])

        if depotPath:
            dirs = self.p4.run_dirs(p4path)
        else:
            dirs = self.p4.run_dirs('-H', p4path)

        self.populateSubDir()

        # for dir in dirs:
        #     # dirName = os.path.basename(dir['dir'])
        #     # subDir = '/'.join( [rootdir, dirName] )
        #     self.rootItem.appendFolderItem(dir['dir'])

        #     files = p4Filelist(self.p4, dir['dir'], findDeleted)

        #     for f in files:
        #         self.rootItem.appendFileItem( f['name'], f['type'], f['time'], f['action'], f['change'] )

        # for i in range(self.rootrowcount()):
        #     idx = self.index(i, 0, self.parent(QtCore.QModelIndex()))
        #     treeItem = idx.internalPointer()

        #     self.populateSubDir(idx)

    def populateSubDir(self, idx=None, root="//depot", findDeleted=False):
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

        depotPath = "depot" in root

        dirpath = '/'.join([p4path,'*'])

        self.p4.exception_level = 1
        if depotPath:
            p4subdirs = self.p4.run_dirs(dirpath)
        else:
            p4subdirs = self.p4.run_dirs('-H', dirpath)


        p4subdirs = [child['dir'] for child in p4subdirs]
        Utils.p4Logger().debug('p4.run_dirs(%s) = %s' % (p4path, p4subdirs) )

        for p4child in p4subdirs:
            Utils.p4Logger().debug(p4child)
            treeItem.appendFolderItem(p4child)

        p4subfiles = self.p4.run_fstat(dirpath)
        Utils.p4Logger().debug('p4FileList = %s' % p4subfiles )

        for f in p4subfiles:
            fullpath = f['depotFile' if depotPath else 'clientFile']
            action = f['headAction']
            change = f['haveRev']
            time = f['headTime']
            filetype = f['headType']
            treeItem.appendFileItem( fullpath, filetype, time, action, action )
            # fileName = os.path.basename(f['name'])
            # data = [fileName, f['type'], f['time'], f['action'], f['change'], f['name']]

            # fileData = TreeItem(data, childData)
            # childData.appendChild(fileData)
        Utils.p4Logger().debug('\n\n')

    # def populate(self, rootdir, findDeleted=False):
    #     rootdir = rootdir.replace('\\', '/')

    #     print "Scanning subfolders in {0}...".format(rootdir)

    #     import maya.cmds as cmds
    #     cmds.refresh()

    #     def scanDirectoryPerforce(root, treeItem):
    #         change = p4.run_opened()

    #         for item in perforceListDir(root):
    #             itemPath = "{0}/{1}".format(root, item['name'] ) # os.path.join(root, item)
    #             # print "{0}{1}{2}".format( "".join(["\t" for i in range(depth)]), '+'
    #             # if perforceIsDir(itemPath) else '-', item['name'] )
    #             data = [ item['name'], item['type'], item['time'], item['change'] ]

    #             childDir = TreeItem( data, treeItem)
    #             treeItem.appendChild( childDir )

    #             tmpDir = TreeItem( [ "TMP", "", "", "" ], childDir )
    #             childDir.appendChild( None )

    #             print itemPath, perforceIsDir( itemPath )
    #             if perforceIsDir( itemPath ):
    #                 scanDirectoryPerforce(itemPath, childDir)

    #     def scanDirectory(root, treeItem):
    #         for item in os.listdir(root):
    #             itemPath = os.path.join(root, item)
    #             # print "{0}{1}{2}".format( "".join(["\t" for i in range(depth)]), '+' if os.path.isdir(itemPath) else '-', item)
    #             childDir = TreeItem( [item], treeItem)
    #             treeItem.appendChild( childDir )
    #             if os.path.isdir( itemPath ):
    #                 scanDirectory(itemPath, childDir)

    #     scanDirectoryPerforce(rootdir, self.rootItem )

    #     print dirName
    #     directory = "{0}:{1}".format(i, os.path.basename(dirName))
    #     childDir = TreeItem( [directory], self.rootItem)
    #     self.rootItem.appendChild( childDir )

    #     for fname in fileList:
    #        childFile = TreeItem(fname, childDir)
    #        childDir.appendChild([childFile])

    #     for i,c  in enumerate("abcdefg"):
    #         child = TreeItem([i],self.rootItem)
    #         self.rootItem.appendChild(child)

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

                if itemType == "Folder":
                    return QtGui.QIcon(os.path.join(interop.getIconPath(), 'File0059.png'))
                elif "binary" in itemType:
                    return QtGui.QIcon(os.path.join(interop.getIconPath(), 'File0315.png'))
                elif "text" in itemType:
                    return QtGui.QIcon(os.path.join(interop.getIconPath(), 'File0027.png'))
                else:
                    return QtGui.QIcon(os.path.join(interop.getIconPath(), 'File0106.png'))

                icon = QtGui.QFileIconProvider(QtGui.QFileIconProvider.Folder)
                return icon
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

    def emitDataChanged(self, idx):
        self.dataChanged.emit(idx, idx)