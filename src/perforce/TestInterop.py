from version import __version__
from BaseInterop import BaseInterop


class TestInterop(BaseInterop):

    @staticmethod
    def setupTestingEnvironment():
        pass

    @staticmethod
    def main_parent_window():
        return None

    @staticmethod
    def createMenu(entries):
        print 'Initialising menu...'

        def fillMenu(entries, indent=0):
            debugIndent = '\t' * indent

            for entry in entries:
                if entry.get('divider'):
                    # Create divider
                    print debugIndent,
                    if entry.get('label'):
                        print entry['label'],
                    print '-'*50

                elif entry.get('entries'):
                    # Create submenu
                    print debugIndent,
                    print '>>>',
                    if entry.get('label'):
                        print entry['label']

                    fillMenu(entry['entries'], indent+1)
                elif entry.get('command'):
                    # Add an entry
                    print debugIndent,
                    print '|' + entry.get('label')
                else:
                    raise ValueError('Unknown entry type')

            # Add a readonly version entry
            print debugIndent,
            print '|' + __version__

        fillMenu(entries, debugPrint=batchmode)

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
