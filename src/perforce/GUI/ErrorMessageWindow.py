from Qt import QtCore, QtGui, QtWidgets
from perforce.DCCInterop import interop

def displayErrorUI(e):
    error_ui = QtGui.QMessageBox()
    error_ui.setWindowFlags(QtCore.Qt.WA_DeleteOnClose)

    eMsg, type = Utils.parsePerforceError(e)

    if type == "warning":
        error_ui.warning(interop.main_parent_window(), "Perforce Warning", eMsg)
    elif type == "error":
        error_ui.critical(interop.main_parent_window(), "Perforce Error", eMsg)
    else:
        error_ui.information(interop.main_parent_window(), "Perforce Error", eMsg)

    error_ui.deleteLater()