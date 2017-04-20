import unittest

from perforce.DCCInterop import interop
from perforce.GUI import PerforceMenu

from test_perforce import TestingEnvironment

class PerforceUITests(unittest.TestCase):
    def setUp(self):
    	print repr(interop)
        interop.setupTestingEnvironment()
        
        self.p4 = TestingEnvironment()        
        self.menu = PerforceMenu.MainShelf(self.p4)

    def testOne(self):
        self.failUnless(True)
