import unittest
import logging

from perforce.AppInterop import interop
from perforce.GUI import initMenu

from test_perforce import TestingEnvironment


class PerforceUITests(unittest.TestCase):
    def setUp(self):
        window, app = interop.setupTestingEnvironment()
        logging.basicConfig(level=logging.DEBUG)

        self.p4 = TestingEnvironment()
        initMenu(self.p4)

        # window.show()
        # app.exec_()

    def testOne(self):
        self.failUnless(True)
