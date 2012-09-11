# Check in setParaValue() for list/integer type 
import types

# Define Exception Class
class SlowCtrlParamsInvalidRangeError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)

class SlowCtrlParams(object):
 
    def __init__(self):
#    def __init__(self, xmlObject, fromFile=False, strict=True):
        #TODO: Sort out argument list - will have implications wherever objects are created of this class
        strict = True
        # Set the strict syntax flag to specified value (defaults to true)
        self.strict = strict
    
    #   paramsDict = {'dictKey'                     : [width, posn, value(s)}    
        self.paramsDict = {'mux_decoder_default'         : [3, -1, -1],
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
        # Definition of position of fast command fields in BRAM words
        self.sync = 1
        self.sync_pos = 21
        self.nop_pos  = 22
        self.cmd_pos  = 12
        self.sync_reset_pos = 2

        # Count total number of nops
        self.total_number_nops = 0
        
        # Count total number of words
        self.total_number_words = 0
                
        # Parse the XML specified, either from a file if the fromFile flag
        # was set or from the string passed
        if fromFile == True:
            self.tree = ElementTree.parse(xmlObject)
            self.root = self.tree.getroot()
        else:
            self.tree = None 
            self.root = ElementTree.fromstring(xmlObject)
        
        # Get the root of the tree and verify it is an lpd_command_sequence
        if self.root.tag != 'lpd_command_sequence':
            raise LpdCommandSequenceError('Root element is not an LPD command sequence')

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
            
    def parseElement(self, theElement):
        '''
        Parses an element (partial tree) of the XML command sequence, encoding commands
        into the appropriate values and returning them. Note that slow control is more complicated
        because each parameter  is inserted into the slow control bitstream according to its relative position.
        '''
        
        # Initialise empty list to contain binary command values for this part of the tree
        encodedSequence = [0] * 122
        
        # Track number of nops counted locally
        localNopsSum = 0
        
        # Increment tree depth counter
        self.depth = self.depth + 1
        
        # Loop over child nodes of the current element
        for child in theElement:

            # Get the command name (tag) for the current element
            cmd = child.tag
                         
            # Check this command is in the syntax dictionary and process
            # accordingly. Raise an exception if the command is not recognised and
            # strict syntax checking is enabled
            if cmd in self.cmdDict:
            
                # Get count and NOP attributes    
                count = self.getCountAttrib(child)
                
                # Pack command and number of NOPs into binary word with sync bits etc. sync_reset
                # commands are treated as a special case and packed differently. 
                if cmd == 'mux_decoder_default':
                    # This is a default value, unless it is still -1 (not set)
                    cmdParams = self.getParamValue(cmd)
                    if cmdParams[2] == -1:
                        pass
                    else:
                        # Default values set, update the mux decoder settings for the 512 pixels accordingly
                        
                        # Define slow control word width
                        scWordWidth = 3
                        # Track whether it's an edge case (i.e. 32 not evenly divisible by 3)
                        edgeCase = 0
                        # Save the contents of one 32 bit word
                        seqIndex = 0
                        # Track relative position inside the 32-bit word
                        bitCount = 0
                        # Save excess of any slow control word that spans the 32 bit word boundary
                        bitRemainder = 0
                        while bitCount < 32:
                            # How far away from the 32-bit word boundary are we?
                            edgeCase = 32 - bitCount
                            if edgeCase < scWordWidth:
                                # TODO: HANDLE THE EDGE CASES AND UPDATE encodingSeq
                                if edgeCase == 2:
                                    # Save the first 2 bits
                                    currentVal = cmdParam[2] & 3
                                    # Bit shift by bitCount and add
                                    seqIndex += currentVal << bitCount
                                    # Save the remainder
                                    bitRemainder = cmdParam[2] >> 2
                                    # Clear the 32 bit word
                                    seqIndex = 0
                                else:
                                    # Save the first bit
                                    currentVal = cmdParam[2] & 1
                                    # Bit shift by bitCount and add
                                    seqIndex += currentVal << bitCount
                                    # Save the remainder
                                    bitRemainder = cmdParam[2] >> 1
                                    # Clear the 32 bit word
                                    seqIndex = 0
                            elif 0 < bitCount < 3:
                                # Edge case: 1 or 2 bits remain from previous 32-bit word 
                                pass
                            else:
                                # Bit shift running sum by relative position within 32-bit word
                                currentVal = cmdParam[2] << bitCount
                                # Add the current 3-bit word
                                seqIndex += currentVal
                                # Increment counter by 3 (bits)
                                bitCount += scWordWidth
#                else:
                cmdWord = (self.sync << self.sync_pos) | (self.cmdDict[cmd] << self.cmd_pos)
            
                    
                # Add in the NOPs to the command word. If the command itself is a NOP, use
                # the count attribute to specify how many NOPs to add. Also reset count to
                # 1 to avoid injecting repeated individual NOPs into the encoded sequence
                #TODO: nop is redundant, remove this:
                if cmd == 'nop':
                    if nops > 0:
                        raise LpdCommandSequenceError('NOPs atttribute specified for NOP command, use count attribute instead')
                    
                    cmdWord = (count - 1 << self.nop_pos) | cmdWord
                    # Count number of nops
                    localNopsSum += count
                    count = 1
                    
                else:
                    cmdWord = (nops << self.nop_pos) | cmdWord
                    # Count number of nops if specified
                    if nops > 0:
                        localNopsSum += nops
            
                
                # Append packed command word to the encoded sequence the number of times
                # specified by the count attribute
                encodedSequence.extend([cmdWord] * count)
                                                            
            else:
                if self.strict:
                    raise LpdCommandSequenceError('Illegal command %s specified' % (child.tag))
            
        # Back up one level in the tree              
        self.depth = self.depth - 1
        
        # Return the encoded sequence for this (partial) tree
        return localNopsSum, encodedSequence
 

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

