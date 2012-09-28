'''
Created on 25 Sep 2012

@author: tcn
'''
import unittest
from LpdDeviceParameters import *

class Test(unittest.TestCase):


    def setUp(self):
        self.params = LpdDeviceParameters()
        pass


    def tearDown(self):
        pass

    def testPrintNumberOfParams(self):
        print "LpdDeviceParameters has", len(self.params.parameters), 'parameters'

    def testGenerateParameters(self):
        for paramTemplate in self.params.parameterTemplateStr('expected'):
            print paramTemplate
            print

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()