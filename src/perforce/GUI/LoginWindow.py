import os

from P4 import P4, P4Exception
from Qt import QtCore, QtGui, QtWidgets

from ErrorMessageWindow import displayErrorUI

def setupConnection(p4):
    try:
        firstTimeLogin( enterUsername=p4.user is None,
                        enterPassword=p4.password is None)
    except P4Exception as e:
        # If user/pass is set but it fails anyway, try a last ditch attempt
        # to let the user input their stuff
        try:
            self.firstTimeLogin(p4,
                                enterUsername=p4.user is None,
                                enterPassword=True)
        except P4Exception as e:
            raise e


def firstTimeLogin(self, p4, enterUsername=True, enterPassword=True, parent=None, *args):
    username = None
    password = None

    if enterUsername:
        username, ok = QtWidgets.QInputDialog.getText(
            parent,
            "Enter username",
            "Username:",
            QtWidgets.QLineEdit.Normal
            )

        if not username or not ok:
            raise ValueError("Invalid username")

        p4.user = str(username)

    if enterPassword:
        password, ok = QtWidgets.QInputDialog.getText(
            parent,
            "Enter password",
            "Password:",
            QtWidgets.QLineEdit.Password)

        if not password or not ok:
            raise ValueError("Invalid password")

        p4.password = str(password)

    # Validate SSH Login / Attempt to login
    try:
        Utils.p4Logger().info(p4.run_login("-a"))
    except P4Exception as e:
        regexKey = re.compile(ur'(?:[0-9a-fA-F]:?){40}')
        # regexIP = re.compile(ur'[0-9]+(?:\.[0-9]+){3}?:[0-9]{4}')
        errorMsg = str(e).replace('\\n', ' ')

        key = re.findall(regexKey, errorMsg)
        # ip = re.findall(regexIP, errorMsg)

        if key:
            Utils.p4Logger().info(p4.run_trust("-i", key[0]))
            Utils.p4Logger().info(p4.run_login("-a"))
        else:
            raise e

    if username:
        Utils.writeToP4Config(p4.p4config_file,
                              "P4USER", str(username[0]))

    # if password:
    #     Utils.writeToP4Config(p4.p4config_file,
    #                           "P4PASSWD", str(password[0]))