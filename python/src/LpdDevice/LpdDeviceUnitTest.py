'''
Created on 18 Sep 2012

@author: tcn
'''
import unittest
from LpdDevice.LpdDevice import * 

class Test(unittest.TestCase):


    def setUp(self):
        simulateFemClient = True
        self.lpdDevice = LpdDevice(simulateFemClient)
        rc = self.lpdDevice.open('127.0.0.1', 6969)
        self.assertEqual(rc, LpdDevice.ERROR_OK)
        
    def tearDown(self):
        self.lpdDevice.close()

    def testLegalParamSet(self):
        rc = self.lpdDevice.paramSet('sensorBias', 127.3) 
        self.assertEqual(rc, LpdDevice.ERROR_OK, 'legal parameter set failed, error code %d: %s' % (rc, self.lpdDevice.errorStringGet()))
        
    def testIllegalParamSet(self):
        rc =self.lpdDevice.paramSet('wibbleWobble', 3.14)
        self.assertEqual(rc, LpdDevice.ERROR_PARAM_UNKNOWN, 'illegal parameter set did not fail correctly')
        
    def testIllegalParamTypeSet(self):
        rc = self.lpdDevice.paramSet('sensorBias', 'illegalStringVal')
        self.assertEqual(rc, LpdDevice.ERROR_PARAM_ILLEGAL_TYPE, 'illegal parameter value type did not fail correctly')
        
    def testParamSetAndGet(self):
        testVal = 343.134
        rc = self.lpdDevice.paramSet('sensorBias', testVal)
        self.assertEqual(rc, LpdDevice.ERROR_OK, 'legal parameter set failed')
        (rc, result) = self.lpdDevice.paramGet('sensorBias')
        self.assertEqual(rc, LpdDevice.ERROR_OK, 'legal parameter get failed')
        self.assertEqual(result, testVal, 'mismatch between set and get values')
        
    def testUnsetParamGet(self):
        name = 'unsetParam'
        self.lpdDevice.allowedParams[name] =  AttributeContainer(int, 'UnsetParam', 'Unset Parameter', 0, 1000, 100, AccessWrite, AssignmentOptional)
        (rc, result) = self.lpdDevice.paramGet(name)
        del self.lpdDevice.allowedParams[name]
        
        self.assertEqual(rc, LpdDevice.ERROR_PARAM_UNSET, 'failed to trap get of unset parameter')
        self.assertEqual(result, None, 'get of unset parameter did not return None')
        
    def testVectorParamSetAndGet(self):
        name = 'vectorParam'
        testVector = [1, 2, 3, 4, 5000]
        self.lpdDevice.allowedParams[name] = AttributeContainer([int]*len(testVector), 'VectorParam', 'Test Vector Parameter', 0, 0xFFFFFFFF, 0x0, AccessWrite, AssignmentOptional)
        rc = self.lpdDevice.paramSet(name, testVector)
        self.assertEqual(rc, LpdDevice.ERROR_OK, 'Vector parameter set failed: %s' % self.lpdDevice.errorStringGet())
        (rc, result) = self.lpdDevice.paramGet(name)
        self.assertEqual(rc, LpdDevice.ERROR_OK, 'Vector parameter get failed: %s' % self.lpdDevice.errorStringGet())
        self.assertEqual(result, testVector, 'Mismatch between set and get test vector parameter')
        
    def testVectorParamSetWrongLength(self):
        name = 'vectorParam'
        testVector = [1, 2, 3, 4]
        vecLen = len(testVector) + 1
        self.lpdDevice.allowedParams[name] = AttributeContainer([int]*vecLen, 'VectorParam', 'Test Vector Parameter', 0, 0xFFFFFFFF, 0x0, AccessWrite, AssignmentOptional)
        rc = self.lpdDevice.paramSet(name, testVector)
        self.assertEqual(rc, LpdDevice.ERROR_PARAM_VECTOR_LENGTH, 'Vector parameter set failed to identify length mismatch')
        
    def testMinMaxDefinedParamBadValue(self):
        name = 'minMaxDefinedTestParam'
        minVal = 0
        maxVal = 10
        self.lpdDevice.allowedParams[name] = AttributeContainer(int, 'MinMaxDefinedTestParam', 'Min/Max Defined Parameter', minVal, maxVal, 0, AccessWrite, AssignmentOptional)
        illegalVal = 11
        rc = self.lpdDevice.paramSet(name, illegalVal)
        self.assertEqual(rc, LpdDevice.ERROR_PARAM_ILLEGAL_VALUE, 'Failed to trap attempt to set out-of-min/max parameter value')

    def testRangeDefinedParamBadValue(self):
        name = 'rangeDefinedTestParam'
        allowedVals = [0, 3, 5]
        self.lpdDevice.allowedParams[name] = AttributeContainer(int, 'rangeDefinedTestParam', 'rangeDefinedTestParameter', allowedVals, None, 0, AccessWrite, AssignmentOptional)
        illegalVal = 1
        rc = self.lpdDevice.paramSet(name, illegalVal)
        self.assertEqual(rc, LpdDevice.ERROR_PARAM_ILLEGAL_VALUE, 'Failed to trap attempt to set out-of-range parameter value')



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()