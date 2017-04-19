import unittest

import perforce.DCCInterop as DCCInterop
from perforce.GUI import PerforceMenu

from test_perforce import TestingEnvironment

class PerforceUITests(unittest.TestCase):
    def setUp(self):
        DCCInterop.setupTestingEnvironment()
        
        self.p4 = TestingEnvironment()        
        self.menu = PerforceMenu.MainShelf(self.p4)

    def testOne(self):
        self.failUnless(True)
