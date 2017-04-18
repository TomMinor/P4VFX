from PySide import QtCore
from PySide import QtGui

def displayErrorUI(e):
    error_ui = QtGui.QMessageBox()
    error_ui.setWindowFlags(QtCore.Qt.WA_DeleteOnClose)

    eMsg, type = Utils.parsePerforceError(e)

    if type == "warning":
        error_ui.warning(DCCInterop.main_parent_window(), "Perforce Warning", eMsg)
    elif type == "error":
        error_ui.critical(DCCInterop.main_parent_window(), "Perforce Error", eMsg)
    else:
        error_ui.information(DCCInterop.main_parent_window(), "Perforce Error", eMsg)

    error_ui.deleteLater()