'''
Created on 25 Sep 2012

@author: tcn
'''
from __future__ import print_function

import unittest
from lpd.device.device_parameters import *

class Test(unittest.TestCase):


    def setUp(self):
        self.params = LpdDeviceParameters()
        pass


    def tearDown(self):
        pass

    def testPrintNumberOfParams(self):
        print("LpdDeviceParameters has", len(self.params.expectedParameters), 'parameters')

    def testGenerateParameters(self):
        for paramTemplate in self.params.parameterTemplateStr('expected'):
            print(paramTemplate)
            print()

if __name__ == "__main__":
    unittest.main()