import unittest
import logging
import os

from test_perforce import TestingEnvironment, setupEnvironment
setupEnvironment()

from perforce.Utils import p4Logger
from perforce.AppInterop import interop
from perforce.GUI import initMenu


def setup():
    cwd = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    os.environ["P4CONFIG"] = os.path.join(cwd, '.p4config')

    window, app = interop.setupTestingEnvironment()
    logging.basicConfig(level=logging.DEBUG)

    p4 = TestingEnvironment()

    p4Logger().debug( 'Default cwd: %s' % p4.cwd )

    initMenu(p4)

    window.show()
    app.exec_()

if __name__ == '__main__':
    setup()