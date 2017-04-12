import unittest

# import Perforce.PerforceUI
# from Perforce.MayaInterop import MayaInterop as DCCInterop

class PerforceUITests(unittest.TestCase):
    def setUp(self):
        DCCInterop.setupTestingEnvironment()

    def testOne(self):
        self.failUnless(False)

if __name__ == '__main__':
    unittest.main()