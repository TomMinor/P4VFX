import unittest

from perforce.AppInterop import interop
from perforce.GUI import PerforceMenu

from test_perforce import TestingEnvironment

class PerforceUITests(unittest.TestCase):
    def setUp(self):
        app = interop.setupTestingEnvironment()
        
        self.p4 = TestingEnvironment()
        self.menu = PerforceMenu.MainShelf(self.p4)
        self.menu.addMenu()

        app.exec_()

    def testOne(self):
        self.failUnless(True)
