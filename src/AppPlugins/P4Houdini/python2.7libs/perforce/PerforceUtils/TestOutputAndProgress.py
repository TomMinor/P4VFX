from P4 import P4, P4Exception, Progress, OutputHandler

import perforce.Utils as Utils
from perforce.AppInterop import interop

class TestOutputAndProgress(Progress, OutputHandler):

    def __init__(self, ui):
        Progress.__init__(self)
        OutputHandler.__init__(self)
        self.totalFiles = 0
        self.totalSizes = 0
        self.ui = ui
        self.ui.setMinimum(0)
        self.ui.setHandler(self)

        self.shouldCancel = False

    def setCancel(self, val):
        self.shouldCancel = val

    def outputStat(self, stat):
        if 'totalFileCount' in stat:
            self.totalFileCount = int(stat['totalFileCount'])
            Utils.p4Logger().debug("TOTAL FILE COUNT: %s" % (self.totalFileCount))
        if 'totalFileSize' in stat:
            self.totalFileSize = int(stat['totalFileSize'])
            Utils.p4Logger().debug("TOTAL FILE SIZE: %s" % (self.totalFileSize))
        if self.shouldCancel:
            return OutputHandler.REPORT | OutputHandler.CANCEL
        else:
            return OutputHandler.HANDLED

    def outputInfo(self, info):
        interop.refresh()
        Utils.p4Logger().debug("INFO: %s" % (info))
        if self.shouldCancel:
            return OutputHandler.REPORT | OutputHandler.CANCEL
        else:
            return OutputHandler.HANDLED

    def outputMessage(self, msg):
        interop.refresh()
        Utils.p4Logger().debug("Msg: %s" % (msg))

        if self.shouldCancel:
            return OutputHandler.REPORT | OutputHandler.CANCEL
        else:
            return OutputHandler.HANDLED

    def init(self, type):
        interop.refresh()
        Utils.p4Logger().debug("Begin: %s" % (type))
        self.type = type
        self.ui.incrementCurrent()

    def setDescription(self, description, unit):
        interop.refresh()
        Utils.p4Logger().debug("Desc: %s, %s" % (description, unit))
        pass

    def setTotal(self, total):
        interop.refresh()
        Utils.p4Logger().debug("Total: %s" % (total))
        self.ui.setMaximum(total)
        pass

    def update(self, position):
        interop.refresh()
        Utils.p4Logger().debug("Update: %s" % (position))
        self.ui.setValue(position)
        self.position = position

    def done(self, fail):
        interop.refresh()
        Utils.p4Logger().debug("Failed: %s" % (fail))
        self.fail = fail