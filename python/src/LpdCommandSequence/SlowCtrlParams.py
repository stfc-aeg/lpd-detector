# Check in setParaValue() for list/integer type 
import types

# Define Exception Class
class SlowCtrlParamsInvalidRangeError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)

class SlowCtrlParams(object):
 
    numPixels = 3
#   paramsDict = {'dictKey'                     : [width, posn, value(s)}    
    paramsDict = {'mux_decoder_default'         : [3, -1, -1],
                  'mux_decoder'                 : [3, 0, [-1] * 512 ],
                  'feedback_select_default'     : [1, -1, -1],
                  'feedback_select'             : [1, 1536, [-1] * 512],
                  'self_test_decoder_default'   : [3, -1, -1],
                  'self_test_decoder'           : [3, 1537, [-1] * 512 ],
                  'self_test_enable'            : [1, 3584, -1],
                  'daq_bias_default'            : [5, -1, -1],
                  'daq_bias'                    : [5, 3585, [-1] * 47],
                  'spare_bits'                  : [5, 3820, -1],        # Special Case: 5 bits cover everything
                  '100x_filter_control'         : [20, 3825, -1],       # Special Case: 20 bits cover everything
                  'adc_clock_delay'             : [20, 3845, -1],       # Special Case: 20 bits cover everything
                  'digital_control'             : [40, 3865, -1],       # Special Case: 40 bits cover everything
                  }
     
    def __init__(self):
        
        pass

    def getParamValue(self, dictKey):
        """ Obtains the three variables associated with the dictionary key 'dictKey' 
            and returns them as three variables (the third are in some cases a list) """
        
        width = 0xdeadbeef
        posn = 0xDeadBeef
        val = 0xDeadBeef
        
        # Does dictKey exist in the dictionary?
        if dictKey in self.paramsDict:
            result = self.paramsDict[dictKey]
            
            width = result[0]
            posn = result[1]
            val = result[2]
        else:
            print "\"" + dictKey + "\" doesn't exist."
        
        return [width, posn, val]
 
    def setParamValue(self, dictKey, index, value):
        """ updates the dictionary key 'dictKey' with the new value in 'value', 
            overwriting whatever used to be at position 'index' """
            
        # Does dictKey exist in the dictionary?
        if dictKey in self.paramsDict:
                        
            # Save the current key's values that we (may) want to retain
            currentValue = self.paramsDict[dictKey]
            
#            print "\trange check: ", 0, " value: ", value, " max: ", (2**currentValue[0])
            # Check that the new value is within valid range
            if not (0 <= value <= ( (2**currentValue[0]) -1) ):
                raise SlowCtrlParamsInvalidRangeError("Key %s's new value outside valid range" % dictKey)
#                print "\tnew value is outside valid range!"
            
            else:
                # Is the third variable a list or an integer?
                if isinstance(currentValue[2], types.ListType):
                    # it's a list; Update the new value
                    currentValue[2][index] = value
                    
                elif isinstance(currentValue[2], types.IntType):
                    currentValue[2] = value
                else:
                    print "SetParamValue() Error: currentValue[2] is neither a list nor an integer!"
                                    
                # Overwrite the old value
                self.paramsDict[dictKey] = currentValue

        else:
            print "\"" + dictKey + "\" doesn't exist."

import unittest
    
class SlowCtrlParamsTest(unittest.TestCase):
    '''
    Unit test class for SlowCtrlParams.
    '''
    
    def testStringParse(self):
        '''
        Tests that updating a parameter works as expected
        '''
        
        # setParamValue(dictKey, index, value)
        dictKey = "self_test_decoder_default"
        index = 0
        value = 7

        # Expected encoded values
        expectedVals = [3, -1, value]
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams()
        paramsObj.setParamValue(dictKey, index, value)
        
        newVals = paramsObj.getParamValue(dictKey)

        # Test that intended value matches expected
        self.assertEqual(newVals, expectedVals, 'testStringParse() failed to update key as expected')

        # 'daq_bias'                    : [5, 3585, [-1] * 47],
        dictKey = 'daq_bias'
        index = 5
        value = 31
        
        expectedVals = paramsObj.getParamValue(dictKey)
        expectedVals[2][index] = value
        
        paramsObj.setParamValue(dictKey, index, value)
        newVals = paramsObj.getParamValue(dictKey)

        self.assertEqual(newVals, expectedVals, 'testStringParse() failed to update key as expected')

    def testOutOfRangeKeyValueFails(self):
        '''
        Tests that updating a parameter will fail if value exceeds valid range
        '''
        
        # setParamValue(dictKey, index, value)
        dictKey = "self_test_decoder_default"
        index = 0
        value = 8
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams()
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "self_test_decoder"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "mux_decoder_default"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "mux_decoder"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)
        
        # Test 1 bit widths
        dictKey = "feedback_select_default"
        value = 2
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "feedback_select"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "self_test_enable"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        # Test 5 bit widths
        dictKey = "daq_bias_default"
        value = 32
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "daq_bias"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "spare_bits"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        # Test 20 bit width
        dictKey = "100x_filter_control"
        value = 1048575+1
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)
        
        dictKey = "adc_clock_delay"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        # Test 40 bit width
        dictKey = "digital_control"
        value = 1099511627776
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)
        
if __name__ == '__main__':
    
    
    # Execute unit testing
    unittest.main()
    
    ''' Manual testing '''
#    theParams = SlowCtrlParams()
#    
##    theParams.getParamValue("mux_decoder_default")
#    width, posn, val = theParams.getParamValue("self_test_decoder_default")
#    print "Before: ", width, posn, val, "...", 
#    
#    print "Changing self_test_decoder_default.."
#    theParams.setParamValue("self_test_decoder_default", 1, 56)
#     
#    width, posn, val = theParams.getParamValue("self_test_decoder_default")
#    print "After: ", width, posn, val
#
#    print "-=-=-=-=-=-"
#    
#    width, posn, val = theParams.getParamValue("daq_bias")
#    print "Before: ", width, posn, val, "...", 
#    
#    print "Changing daq_bias.."
#    theParams.setParamValue("daq_bias", 11, 28)
#    
#    width, posn, val = theParams.getParamValue("daq_bias")
#    print "After:  ", width, posn, val

