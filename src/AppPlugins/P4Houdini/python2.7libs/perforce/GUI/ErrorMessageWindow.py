from qtpy import QtCore, QtGui, QtWidgets
from perforce.AppInterop import interop
from perforce import PerforceUtils

def displayErrorUI(e):
    error_ui = QtWidgets.QMessageBox()
    error_ui.setWindowFlags(QtCore.Qt.WA_DeleteOnClose)

    eMsg, type = PerforceUtils.parsePerforceError(e)

    if type == "warning":
        error_ui.warning(interop.main_parent_window(), "Perforce Warning", eMsg)
    elif type == "error":
        error_ui.critical(interop.main_parent_window(), "Perforce Error", eMsg)
    else:
        error_ui.information(interop.main_parent_window(), "Perforce Error", eMsg)

    error_ui.deleteLater()