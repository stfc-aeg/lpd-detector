# Check in setParaValue() for list/integer type 
import types, sys

from xml.etree.ElementInclude import ElementTree
from xml.etree.ElementTree import ParseError

# Define Exception Class
class SlowCtrlParamsInvalidRangeError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)

class SlowCtrlParamsError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)

class SlowCtrlParams(object):
 
#    def __init__(self):
    def __init__(self, xmlObject, fromFile=False, strict=True):
        #TODO: Sort out argument list - will have implications wherever objects are created of this class
        strict = True
        # Set the strict syntax flag to specified value (defaults to true)
        self.strict = strict
        
        ''' Debug info: '''
        self.bDebug = False

        if self.bDebug:
            print "debugging enabled."

    #   paramsDict = {'dictKey'                     : [width, posn, value(s), [bPixelTagRequired, bValueTagRequired, bIndexTagRequired]}
        self.paramsDict = {'mux_decoder_default'         : [3,  -1,     -1,         [False, True, False]],
                           'mux_decoder'                 : [3,  0,      [-1] * 512, [True,  True, False]],
                           'feedback_select_default'     : [1,  -1,     -1,         [False, True, False]],
                           'feedback_select'             : [1,  1536,   [-1] * 512, [True,  True, False]],
                           'self_test_decoder_default'   : [3,  -1,     -1,         [False, True, False]],
                           'self_test_decoder'           : [3,  1537,   [-1] * 512, [True,  True, False]],
                           'self_test_enable'            : [1,  3584,   -1,         [False, True, False]],
                           'daq_bias_default'            : [5,  -1,     -1,         [False, True, False]],
                           'daq_bias'                    : [5,  3585,   [-1] * 47,  [False, True, True]],
                           'spare_bits'                  : [5,  3820,   -1,         [False, True, False]],        # Special Case: 5 bits cover everything
                           '100x_filter_control'         : [20, 3825,   -1,         [False, True, False]],       # Special Case: 20 bits cover everything
                           'adc_clock_delay'             : [20, 3845,   -1,         [False, True, False]],       # Special Case: 20 bits cover everything
                           'digital_control'             : [40, 3865,   -1,         [False, True, True]],       # Special Case: 40 bits cover everything
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
        
        ''' Debug information '''
        if self.bDebug:
            print "Class initialising, reading file or string = "
            print xmlObject
            
        #TODO: Implemented this:
        # Parse the XML specified, either from a file if the fromFile flag
        # was set or from the string passed
        if fromFile == True:
            self.tree = ElementTree.parse(xmlObject)
            self.root = self.tree.getroot()
        else:
            self.tree = None 
            self.root = ElementTree.fromstring(xmlObject)
        
        # Get the root of the tree and verify it is an lpd_command_sequence
        if self.root.tag != 'lpd_slow_ctrl_sequence':
            raise SlowCtrlParamsError('Root element is not an LPD slow control command')

        

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
            tags = result[3]
        else:
            print "\"" + dictKey + "\" doesn't exist."
        
        return [width, posn, val, tags]
 
    def setParamValue(self, dictKey, index, value):
        """ updates the dictionary key 'dictKey' with the new value in 'value', 
            overwriting whatever used to be at position 'index'
            
            Note: Python starts any list with 0, therefore first pixel = 0, second pixel = 1, etc.
                (Slow Control documentation states pixel 1 is the first, but disregard that)
        """
                        
        # Does dictKey exist in the dictionary?
        if dictKey in self.paramsDict:
                        
            # Save the current key's values that we (may) want to retain
            currentValue = self.paramsDict[dictKey]

            # Check that the new value is within valid range
            if not (0 <= value <= ( (2**currentValue[0]) -1) ):
                raise SlowCtrlParamsInvalidRangeError("%s's value outside valid range, max: %i received: %i" % (dictKey, 2**currentValue[0]-1, value) )
            
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
            
    def encode(self):
        '''
        Encodes the  slow control command(s)..
        '''

        # Intialise tree depth (used for debugging only)
        self.depth = 0
        
        # Parse the tree, starting at the root element, obtaining the packed
        #     binary command sequence as a list
#        sequence  = self.parseElement(self.root)
        self.parseElement(self.root)
        
        #TODO: sort this out; sequence should come from the buildBitstream() function ??
        sequence  = self.buildBitstream()
        
        # Count the total number of words
        self.total_number_words = len(sequence)
        
        # Return the command sequence
        return sequence

    def getAttrib(self, theElement, theAttrib):
        '''
        Returns the value of the theAttrib attribute of the specified element if it exists,
        or a default value of 1 if not. Can also throw an exception if a non-integer
        attribute is detected
        '''
        if self.bDebug:
            print "attrib: '" + theAttrib + "'",
        
        # Get the attribute or a default value of -2 (differentiate from unspecified value which is -1)
        intAttrib = theElement.get(theAttrib, default='-2')
        
        if self.bDebug:
            print " is: ", intAttrib + ".",
        # Convert count to integer or raise an exception if this failed
        try:
            attrib = int(intAttrib)
        except ValueError:
            raise SlowCtrlParamsError('Non-integer attribute specified')
        
        # Return integer attrib value    
        return attrib

        
    def parseElement(self, theElement):
        '''
            Parses an element (partial tree) of the XML command sequence, encoding commands
            into the appropriate values and returning them. Note that slow control is more complicated
            because each parameter is inserted into the slow control bitstream according to its relative position.
            
            NOTE: pixels run 1-512, index 1-47 but to match Python's lists they're numbered 0-511, 0-46.
        '''
        
        # Initialise empty list to contain binary command values for this part of the tree
#        encodedSequence = [0] * 122
        # Track position within encodedSequence list
#        seqPosition = 0
        
        # Increment tree depth counter
        self.depth = self.depth + 1

        # The structure of the parameters to dictionary is:
        # paramsDict = {'dictKey' : [width, posn, value(s), [bPixelTagRequired, bValueTagRequired, bIndexTagRequired]}
        #     where values(s) is an integer or a list and the nested list of booleans defines which tags that are required
        
        # Loop over child nodes of the current element
        for child in theElement:

            # Get the command name (tag) for the current element
            cmd = child.tag
                         
            # Check this command is in the syntax dictionary and process
            # accordingly. Raise an exception if the command is not recognised and
            # strict syntax checking is enabled
            if cmd in self.paramsDict:

                if self.bDebug:
                    print "\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
                    print "found: ", cmd,
                
                # get parameter values
                pmValues = self.getParamValue(cmd)

                # Extract required tags
                bPixel = pmValues[3][0]
                bValue = pmValues[3][1]
                bIndex = pmValues[3][2]
                
                # Fail if there is no bValue present
                # Get value attribute (always present)
                value = self.getAttrib(child, 'value')
                if value == -2:
                    raise SlowCtrlParamsError("Unable to find the required value tag!")
                
                if self.bDebug:
                    print "value = ", value,
                
                # is there a pixel tag?
                if bPixel:
                    # Get pixel
                    pixel = self.getAttrib(child, 'pixel')
                    if self.bDebug:
                        print " pixel = ", pixel,
                    # Update pixel entry of the dictionary key
                    self.setParamValue(cmd, pixel, value)
                else:
                    # Is there a index tag?
                    if bIndex:
                        index = self.getAttrib(child, 'index')
                        if self.bDebug:
                            print " index = ", index
                        # Update index entry of the dictionary key
                        self.setParamValue(cmd, index, value)
                    else:
                        # No pixel, no index tags: therefore the key value
                        #     is a simple integer to update
                        self.setParamValue(cmd, 0, value)
                
            else:
                if self.strict:
                    raise SlowCtrlParamsError('Illegal command %s specified' % (child.tag))
        
        if self.bDebug:
            print "\n~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~"
        
        # Dictionary now updated, check keys XX_default and if they are not -1 
        # then their corresponding keys should be updated with whatever value the XX_default key has
        for key in self.paramsDict:
            # Is this a _default key?
            if key.endswith("_default"):
                if self.bDebug:
                    print "Found _default key: ", key, " = ",
                # has its value been changed from -1?
                keyValue = self.getParamValue(key)
                if self.bDebug:
                    print keyValue
                # This is a key that ends with _default, but has it been set?
                
                # Derive corresponding key's name
                pairedKey = key.replace("_default", "")
                pairedKeyValue = self.getParamValue(pairedKey)
                length = len(pairedKeyValue[2])

                # Is XXX_default not specified ?
                if keyValue[2] == -1:
                    # Not set, set it to 0
                    for idx in range(length):
                        # Update only if pixel not explicitly set
                        if pairedKeyValue[2][idx] == -1:
                            # -1 denotes pixel hasn't been explicitly set; update it to 0
                            self.setParamValue(pairedKey, idx, 0)
                    
                else:
                    # It is set; Update any entry not already explicitly set
                    for idx in range(length):
                        # Update only if pixel not explicitly set
                        if pairedKeyValue[2][idx] == -1:
                            # -1 denotes pixel hasn't been explicitly set; go ahead and update it
                            self.setParamValue(pairedKey, idx, keyValue[2])
    
        # Back up one level in the tree              
        self.depth = self.depth - 1
        
        # Return the encoded sequence for this (partial) tree
        
        ''' THIS is empty though! '''
        
#        return encodedSequence
 
    def buildBitstream(self):
        '''
            Loop over dictionary keys and building the word bitstream programmatically
        '''
        
                    
        ''' Debug '''
        print "   -=-=-                                    12345678  -=-=-    12345678"

        ''' Debug variables '''
        debugIdx = 33
        debugComparisonKey = "daq_bias" 
#                    debugComparisonKey = "self_test_decoder"

        # Initialise empty list to contain binary command values for this part of the tree
        encodedSequence = [0] * 122
        # Track position within encodedSequence list
        seqPosition = 0
        
        # Loop over dictionary entries 
        for dictKey in self.paramsDict:
            
            # If it is a XX_default key, do not process it
            if dictKey.endswith("_default"):
                continue
            else:
#                print "Dictionary key %20s" % dictKey, "\t",
                
                # Get dictionary key values
                cmdParams = self.getParamValue(dictKey)
                # Display the first two entries of the list
#                print cmdParams[0], cmdParams[1],
                # Is this a scaler quantity?
                if isinstance(cmdParams[2], types.ListType):
                    # it's a list; display first and last couple of values
#                    print  " [", cmdParams[2][0], cmdParams[2][1], "..", cmdParams[2][-2], cmdParams[2][-1], "]"
#                    # How many elements in the third entry?
#                    print "\t len = ", len(cmdParams[2])
                
                    # word width over this key?
                    keyWidth = cmdParams[0]
                    # Where does current key reside within the (122 * word) sequence?
                    wordPosition = cmdParams[1] / 32
                    # Determine number of entries in the nested list
                    listLength = len(cmdParams[2])
                    
                    # bitPosition tracks the bit position within the 3904 bits long bitstream
                    bitPosition = cmdParams[1] % 32
                    
                    # Initialise bitwiseOffset
#                    bitwiseOffset = 0
                    bitwiseOffset = bitPosition
                    
                    # Key: "self_test_decoder" and "feedback_select" share a 4 bit slow control word
                    #    therefore they become a special case (set to 0 for all other keys)
                    specialCaseOffset = 0
                    # Is this key either of the two special cases?
                    if dictKey.startswith("feedback_select"):
                        print "This is: %25s" % dictKey, " = [", 
                        for idx in range(9):
                            print cmdParams[2][idx],
                        print  " .. ]"
                        specialCaseOffset = 3
                    elif dictKey.startswith("self_test_decoder"):
                        # Because the feedback_select bit sits before the self_test_decoder 3 bits,
                        #    bitwiseOffset must start from the 1 and not 0
                        print "This is: %25s" % dictKey, " = [",
                        for idx in range(9):
                            print cmdParams[2][idx],
                        print  " .. ]"
                        specialCaseOffset = 1
                        # REDUNDANT?
#                        bitwiseOffset = specialCaseOffset
                    
                    bitBucket = [0] * (keyWidth * listLength)
            
                    print dictKey + "'s len(bitBucket): ", len(bitBucket)
            
                    # Loop over all the elements of the nested list and produce a "bit bucket"
                    for idx in range(listLength):
                        
                        pass

                    
                    # Loop over this new list and chop each 32 bits into the encoded sequence
    


                else:
                    ''' if isinstance(cmdParams[2], types.ListType): '''
                    
                    ''' it's just an integer '''

                    pass                
                '''  This Needs to Be Replicated on Both Side of the if isinstance() parts ? '''
                
        ''' Debug '''
        print "   -=-=-                                    12345678  -=-=-    12345678"

 
        # Return the encoded sequence for this (partial) tree
        return encodedSequence

    def generateBitMask(self, numBits):
        '''
            Generates that bit mask to cover the number of bits supplied.
            
            I.e. numBits = 1; returns 1,    2 = > 3, 3 => 7, 4 = > 15
        '''
        
        sum = 0
        for idx in range(numBits):
            sum = sum | (1 << idx)
            
        return sum
    
    def displayDictionaryValues(self):
        '''
            Debug function, used to display the dictionary values
        '''
        if self.bDebug:
            print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
            for cmd in self.paramsDict:
                # Get dictionary key's values
                dictKey = self.getParamValue(cmd)
                
                print "dictKey: ", cmd,
                if len(cmd) < 12:
                    print "\t",
                print " \tpos'n: ", dictKey[1], "\t [",
                # Is the third variable a list or an integer?
                if isinstance(dictKey[2], types.ListType):
                    # it's a list
                    for idx in range(11):
                        if (idx < 5):
                            # Print the first five values
                            print dictKey[2][idx],
                        elif idx == 5:
                            print ", .., ",
                        else:
                            # Print the last five values
                            print dictKey[2][-1*(11-idx)],
    
                elif isinstance(dictKey[2], types.IntType):
                   # it's just an integer
                   print dictKey[2],
                else:
                    print "displayDictionaryValues() Error: dictKey[2] is neither a list nor an integer!"
    
                print "]"


import unittest
    
class SlowCtrlParamsTest(unittest.TestCase):
    '''
    Unit test class for SlowCtrlParams.
    '''

    """    
    def testStringParse(self):
        '''
        Tests that updating a parameter works as expected
        '''
        
        daqBiasIdx47 = 11
        daqBiasDefault = 31
        selfTestDecoderDefault = 7
        digitalControlIdx3 = 18

        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <self_test_decoder pixel="1" value="5"/>
                                <self_test_decoder_default value="%i"/>
                                <mux_decoder pixel="2" value="0"/>
                                <mux_decoder_default value="3"/>
                                <daq_bias index="46" value="%i"/>
                                <daq_bias_default value="%i"/>
                                <daq_bias index="2" value="0"/>
                                <digital_control index="3" value="18"/>
                                <spare_bits value="%i"/>
                            </lpd_slow_ctrl_sequence>
        ''' % (selfTestDecoderDefault, daqBiasIdx47, daqBiasDefault, digitalControlIdx3)

  
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        paramsObj.encode()

        # Display an excerp of each dictionary key's value:
        paramsObj.displayDictionaryValues()
  
        # Setup and compare the unit tests..        
        dictKey = "self_test_decoder_default"
        index = 0
        value = selfTestDecoderDefault
        
        # Expected encoded values
        expectedVals = [3, -1, value, [False, True, False]]
        # The actual values
        selfTestDecoderDefaultVals = paramsObj.getParamValue(dictKey)

#        print selfTestDecoderDefaultVals, "\n", expectedVals
        self.assertEqual(selfTestDecoderDefaultVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)

        # 'self_test_decoder'                    : [5, 3585, [-1] * 47],
        dictKey = 'self_test_decoder'
        index = 1
        value = 5
        
        expectedVals = [3, 1537, [selfTestDecoderDefault] * 512, [True, True, False]]
        expectedVals[2][index] = value
        
        self_test_decoderVals = paramsObj.getParamValue(dictKey)
        
#        print self_test_decoderVals, "\n", expectedVals
        self.assertEqual(self_test_decoderVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)
        

        # daq_bias_default
        dictKey = "daq_bias_default"
        index = 0
        value = daqBiasDefault
        
        expectedVals = [5, -1, value, [False, True, False]]
        
        daqBiasDefaultVals = paramsObj.getParamValue(dictKey)
        
#        print daqBiasDefaultVals, "\n", expectedVals
        self.assertEqual(daqBiasDefaultVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)
        
        # 'daq_bias'                    : [5, 3585, [-1] * 47],
        dictKey = 'daq_bias'
        index = 5
        value = daqBiasIdx47
        
        expectedVals = [5, 3585, [daqBiasDefault] * 47, [False, True, True]]
        expectedVals[2][2] = 0
        expectedVals[2][47-1] = value
        
        daq_biasVals = paramsObj.getParamValue(dictKey)

#        print daq_biasVals, "\n", expectedVals
        self.assertEqual(daq_biasVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)

        # 'digital_control'
        dictKey = 'digital_control'
        index = 3
        value = digitalControlIdx3
        
        expectedVals = [40, 3865, value, [False, True, True]]
        expectedVals[2] = value

        digitalControlVals = paramsObj.getParamValue(dictKey)
        
#        print digitalControlVals, "\n", expectedVals
        self.assertEqual(digitalControlVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)

    def testOutOfRangeKeyValueFails(self):
        '''
        Tests that updating a parameter will fail if value exceeds valid range
        '''

        # Strictly not necessary except for the class constructor requiring a XML file or string
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="testOutOfRangeKeyValueFails">
                                <self_test_decoder_default value="7"/>
                            </lpd_slow_ctrl_sequence>
        '''        
        # setParamValue(dictKey, index, value)
        dictKey = "self_test_decoder_default"
        index = 0
        value = 8
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
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
    
    """
    """
    def testSelfTestDecoderDefaultSetValueSeven(self):
        '''
            Test that the key self_test_decoder_default works
        '''
            
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <self_test_decoder_default value="7"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # Display an excerp of each dictionary key's value:
        paramsObj.displayDictionaryValues()        

        # Construct a list of how sequence should look like
        expectedSequence = [0] * 122
        for idx in range(48,112):
            expectedSequence[idx] = 0xEEEEEEEE

        # Toggle display of debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            
            for idx in range(len(encSeq)):
                if (idx % 8 == 0):
                    print "\n%3i: " % idx,
                print "%9X" % encSeq[idx],
            print "\n"
    
    
            print "expectedSequence: (len)", len(expectedSequence)
            
            for idx in range(len(expectedSequence)):
                if (idx % 8 == 0):
                    print "\n%3i: " % idx,
                print "%9X" % expectedSequence[idx],
            print "\n"
        
        self.assertEqual(encSeq, expectedSequence, 'testSelfTestDecoderDefaultSetValueSeven() failed !')

    def testFeedbackSelectDefaultSetValueOne(self):
        '''
            Test that the key feedback_select_default works
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <feedback_select_default value="1"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * 122
        for idx in range(48,112):
            expectedSequence[idx] = 0x11111111
        
        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            
            for idx in range(len(encSeq)):
                if (idx % 8 == 0):
                    print "\n%3i: " % idx,
                print "%9X" % encSeq[idx],
    
            print "\nExpected Sequence: (len)", len(expectedSequence)

            for idx in range(len(expectedSequence)):
                if (idx % 8 == 0):
                    print "\n%3i: " % idx,
                print "%9X" % expectedSequence[idx],
            print "\n"
        
        self.assertEqual(encSeq, expectedSequence, 'testFeedbackSelectDefaultSetValueOne() failed !')

    def testFeedbackSelectAndSelfTestDecoderDefaultsCombined(self):
        '''
            Test that the keys feedback_select_default and self_test_decoder_default work together
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <feedback_select_default value="1"/>
                                <self_test_decoder_default value="2"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * 122
        for idx in range(48,112):
            expectedSequence[idx] = 0x55555555
        
        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            
            for idx in range(len(encSeq)):
                if (idx % 8 == 0):
                    print "\n%3i: " % idx,
                print "%9X" % encSeq[idx],
    
            print "\nExpected Sequence: (len)", len(expectedSequence)

            for idx in range(len(expectedSequence)):
                if (idx % 8 == 0):
                    print "\n%3i: " % idx,
                print "%9X" % expectedSequence[idx],
            print "\n"
        
        self.assertEqual(encSeq, expectedSequence, 'testFeedbackSelectAndSelfTestDecoderDefaultsCombined() failed !')

    def testMuxDecoderDefault(self):
        '''
            Test that the key mux_decoder_default works
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <mux_decoder_default value="5"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * 122
        for idx in range(48):
            indexNo = idx % 3
            if indexNo == 0:
                expectedSequence[idx] = 0x6DB6DB6D
            elif indexNo == 1:
                expectedSequence[idx] = 0xDB6DB6DB
            else:
                expectedSequence[idx] = 0xB6DB6DB6
        
        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            
            for idx in range(len(encSeq)):
                if (idx % 8 == 0):
                    print "\n%3i: " % idx,
                print "%9X" % encSeq[idx],
    
            print "\nExpected Sequence: (len)", len(expectedSequence)

            for idx in range(len(expectedSequence)):
                if (idx % 8 == 0):
                    print "\n%3i: " % idx,
                print "%9X" % expectedSequence[idx],
            print "\n"
        
        self.assertEqual(encSeq, expectedSequence, 'testMuxDecoderDefault() failed !')

    """
    
    def testDaqBiasDefault(self):
        '''
            Test that the key daq_bias_default works
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <daq_bias_default value="31"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * 122
        for idx in range(48):
            indexNo = idx % 3
            if indexNo == 0:
                expectedSequence[idx] = 0x6DB6DB6D
            elif indexNo == 1:
                expectedSequence[idx] = 0xDB6DB6DB
            else:
                expectedSequence[idx] = 0xB6DB6DB6
        
        print "You are actually running the function: testDaqBiasDefault() "
        
        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            
            for idx in range(len(encSeq)):
                if (idx % 8 == 0):
                    print "\n%3i: " % idx,
                print "%9X" % encSeq[idx],
            print "\n"
#            print "\nExpected Sequence: (len)", len(expectedSequence)
#
#            for idx in range(len(expectedSequence)):
#                if (idx % 8 == 0):
#                    print "\n%3i: " % idx,
#                print "%9X" % expectedSequence[idx],
#            print "\n"
        
#        self.assertEqual(encSeq, expectedSequence, 'testDaqBiasDefault() failed !')


    """
    def testSelfTestEnable(self):
        '''
            Test that the key self_test_enable works
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <self_test_enable value="1"/>
                            </lpd_slow_ctrl_sequence>
        '''

        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * 122
        expectedSequence[112] = 0x1

        # Toggle display debug information
        if True:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            
            for idx in range(len(encSeq)):
                if (idx % 8 == 0):
                    print "\n%3i: " % idx,
                print "%9X" % encSeq[idx],
            print "\n"
#            print "\nExpected Sequence: (len)", len(expectedSequence)
#
#            for idx in range(len(expectedSequence)):
#                if (idx % 8 == 0):
#                    print "\n%3i: " % idx,
#                print "%9X" % expectedSequence[idx],
#            print "\n"
        
#        self.assertEqual(encSeq, expectedSequence, 'testSelfTestEnable() failed !')


    def testBuildBitstream(self):
        '''
            Test the buildBitstream function
        '''
        
        daqBiasIdx47 = 11
        daqBiasDefault = 31
        selfTestDecoderDefault = 7
        digitalControlIdx3 = 18

        # ONLY feedback_select
#        stringCmdXml = '''<?xml version="1.0"?>
#                            <lpd_slow_ctrl_sequence name="TestString">
#                                <feedback_select pixel="0" value="1"/>
#                                <feedback_select pixel="2" value="1"/>
#                            </lpd_slow_ctrl_sequence>
#        '''

        # BOTH feedback_select and self_test_decoder
#        stringCmdXml = '''<?xml version="1.0"?>
#                            <lpd_slow_ctrl_sequence name="TestString">
#                                <self_test_decoder_default value="%i"/>
#                                <feedback_select pixel="1" value="1"/>
#                            </lpd_slow_ctrl_sequence>
#        ''' % (selfTestDecoderDefault)

#        stringCmdXml = '''<?xml version="1.0"?>
#                            <lpd_slow_ctrl_sequence name="TestString">
#                                <self_test_decoder_default value="%i"/>
#                                <mux_decoder_default value="5"/>
#                                <mux_decoder pixel="0" value="0"/>
#                                <daq_bias index="46" value="%i"/>
#                                <daq_bias_default value="%i"/>
#                                <daq_bias index="2" value="0"/>
#                                <digital_control index="3" value="18"/>
#                                <spare_bits value="%i"/>
#                            </lpd_slow_ctrl_sequence>
#        ''' % (selfTestDecoderDefault, daqBiasIdx47, daqBiasDefault, digitalControlIdx3)
#                                <self_test_decoder pixel="1" value="5"/>
#                                <feedback_select_default value="0"/>


#        # Parse XML and encode
#        paramsObj = SlowCtrlParams(stringCmdXml)
#        encSeq = paramsObj.encode()
#
#        # Display an excerp of each dictionary key's value:
#        paramsObj.displayDictionaryValues()
#  
#        # Setup and compare the unit tests..        
#        dictKey = "self_test_decoder_default"
#        index = 0
#        value = selfTestDecoderDefault
#        
#
#
#        print "\n\nEncoded Sequence: (len)", len(encSeq)
#        print "       12345678"
#        
#        for idx in range(len(encSeq)):
#            
#            if (idx % 8 == 0):
#                print "\n%3i: " % idx,
#            print "%9X" % encSeq[idx],
#
#        print "\n"
#        print "       12345678"
#        print "\n"

    """

if __name__ == '__main__':
    
    
    # Execute unit testing
    unittest.main()
    
    sys.exit()
    ''' Manual testing '''
    theParams = SlowCtrlParams('sampleSlowControl.xml', fromFile=True)
#    theParams = SlowCtrlParams('simple.xml', fromFile=True)
    
#    theParams.getParamValue("mux_decoder_default")
    width, posn, val, tags = theParams.getParamValue("mux_decoder_default")
#    print "Before: ", width, posn, val, "...", 
    
#    print "Changing self_test_decoder_default.."
#    theParams.setParamValue("mux_decoder_default", 1, 3)
     
#    width, posn, val = theParams.getParamValue("mux_decoder_default")
#    print "After: ", width, posn, val

    theElement = "mux_decoder_default"
    print "\n"
    
    theParams.displayDictionaryValues()
    
    """ Encode XML file into dictionary """
    result = theParams.encode()

    theParams.displayDictionaryValues()
#    for idx in range(122):
#        print "%X\t" % result[idx],
#        if (idx % 6) == 5:
#            print ""
#    print ""
