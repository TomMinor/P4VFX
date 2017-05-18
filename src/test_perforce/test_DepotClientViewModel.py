import unittest
import logging

from perforce.AppInterop import interop
from perforce.GUI import initMenu

from test_perforce import TestingEnvironment
from perforce.GUI import DepotClientViewModel

class DepotClientViewModelTests(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

        self.rootItem = DepotClientViewModel.PerforceItem(None)

    def testAddFileItem(self):
    	testDataIn = [
    			('//depot/subfolder/test0.txt', 'txt', '12:34:56', 'Add', '1'),
    			('//depot/subfolder2/test0.exr', 'exr', '12:34:56', 'Add', '1'),
    			('//depot/subfolder3/test1.txt', 'txt', '12:34:56', 'Add', '1'),
    			]

    	testDataOut = [
    			('test0.txt', 'txt', '12:34:56', 'Add', '1', '//depot/subfolder/test0.txt'),
				('test0.exr', 'exr', '12:34:56', 'Add', '1', '//depot/subfolder2/test0.exr'),
				('test1.txt', 'txt', '12:34:56', 'Add', '1', '//depot/subfolder3/test1.txt')
    			]

    	for data in testDataIn:
    		self.rootItem.appendFileItem(*data)

    	for i, item in enumerate(self.rootItem.childItems):
    		self.failUnless(item.data == testDataOut[i])

    def testAddFolderItem(self):
    	testDataIn = [
    			'//depot/subfolder',
    			'//depot/subfolder/subfolder2',
    			'//depot/subfolder3'
    			]

    	testDataOut = [
    			('subfolder', 'Folder', '', '', '', '//depot/subfolder'),
				('subfolder2', 'Folder', '', '', '', '//depot/subfolder/subfolder2'),
				('subfolder3', 'Folder', '', '', '', '//depot/subfolder3')
    			]
    			
    	for data in testDataIn:
    		self.rootItem.appendFolderItem(data)

    	for i, item in enumerate(self.rootItem.childItems):
    		self.failUnless(item.data == testDataOut[i])