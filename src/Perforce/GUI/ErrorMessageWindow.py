from PySide import QtCore
from PySide import QtGui

def displayErrorUI(e):
    error_ui = QtGui.QMessageBox()
    error_ui.setWindowFlags(QtCore.Qt.WA_DeleteOnClose)

    eMsg, type = Utils.parsePerforceError(e)

    if type == "warning":
        error_ui.warning(mainParent, "Perforce Warning", eMsg)
    elif type == "error":
        error_ui.critical(mainParent, "Perforce Error", eMsg)
    else:
        error_ui.information(mainParent, "Perforce Error", eMsg)

    error_ui.deleteLater()