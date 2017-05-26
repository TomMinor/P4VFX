import tempfile
from perforce.version import __version__

class BaseCallbacks(object):

    @staticmethod
    def validateSubmit():
        raise NotImplementedError

    @staticmethod
    def cleanupCallbacks():
        raise NotImplementedError

    @staticmethod
    def initCallbacks():
        raise NotImplementedError


class BaseInterop(object):
    @staticmethod
    def setupEnvironment():
        pass

    @staticmethod
    def main_parent_window():
        raise NotImplementedError

    @staticmethod
    def createMenu(entries):
        from perforce.AppInterop import interop 

        # We need to import interop so the appropriate class is used while creating the menus
        interop = interop()
        interop.initializeMenu(entries)
        interop.fillMenu(entries)
        interop.addMenuLabel("Version {0}".format(__version__))

    @staticmethod
    def getSettingsPath():
        raise NotImplementedError

    @staticmethod
    def getIconPath():
        raise NotImplementedError

    @staticmethod
    def getSceneFiles():
        return []

    @staticmethod
    def getTempPath():
        return tempfile.gettempdir()

    @staticmethod
    def getCurrentSceneFile():
        raise NotImplementedError

    @staticmethod
    def openScene(filePath):
        raise NotImplementedError

    @staticmethod
    def closeWindow(ui):
        raise NotImplementedError

    @staticmethod
    def refresh():
        raise NotImplementedError

    def initializeMenu(self, entries):
        raise NotImplementedError

    def fillMenu(self, entries):
        for entry in entries:
            if entry.get('divider'):
                self.addMenuDivider(entry.get('label') )
            elif entry.get('entries'):
                self.addMenuSubmenu(entry.get('label'), entry.get('image'), entry['entries'] )
            elif entry.get('command'):
                self.addMenuCommand(entry.get('label'), entry.get('image'), entry.get('command') )
            else:
                raise ValueError('Unknown entry type for \'%s\'' % entry)

    def addMenuDivider(self, menu, label):
        raise NotImplementedError
       
    def addMenuLabel(self, menu, label):
        raise NotImplementedError

    def addMenuSubmenu(self, menu, label, icon, entries):
        raise NotImplementedError

    def addMenuCommand(self, menu, label, icon, command):
        raise NotImplementedError