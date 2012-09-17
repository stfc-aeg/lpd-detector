# Check in setParaValue() for list/integer type 
import types

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
#            print "setParamValue() '%s' " % dictKey, " = ", currentValue
            
#            print "\trange check: ", 0, " value: ", value, " max: ", (2**currentValue[0])
            # Check that the new value is within valid range
            if not (0 <= value <= ( (2**currentValue[0]) -1) ):
                raise SlowCtrlParamsInvalidRangeError("Key %s's new value outside valid range" % dictKey )
#                print "\tnew value is outside valid range!"
            
            else:
                # Is the third variable a list or an integer?
                if isinstance(currentValue[2], types.ListType):
                    # it's a list; Update the new value
#                    print "setPar..() value = ", value, "index: ", index
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
        # binary command sequence as a list
        sequence  = self.parseElement(self.root)
        
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

        # Get the count attribute or a default value of -2 (differentiate from unspecified value which is -1)
        countAttrib = theElement.get(theAttrib, default='-2')
        
        # Convert count to integer or raise an exception if this failed
        try:
            attrib = int(countAttrib)
        except ValueError:
            raise LpdCommandSequenceError('Non-integer attribute specified')
        
        # Return integer attrib value    
        return attrib

        
    def parseElement(self, theElement):
        '''
        Parses an element (partial tree) of the XML command sequence, encoding commands
        into the appropriate values and returning them. Note that slow control is more complicated
        because each parameter is inserted into the slow control bitstream according to its relative position.
        NOTE: pixels run 1-512, index 1-47 put corresponding Python lists run 0-511, 0-46.
            Therefore, when they are updated, their actual values are subtracted by one
        '''
        
        # Initialise empty list to contain binary command values for this part of the tree
        encodedSequence = [0] * 122
        # Track position within encodedSequence list
        seqPosition = 0
        
        # Increment tree depth counter
        self.depth = self.depth + 1
        
        # Loop over child nodes of the current element
        for child in theElement:

            # Get the command name (tag) for the current element
            cmd = child.tag
                         
            # Check this command is in the syntax dictionary and process
            # accordingly. Raise an exception if the command is not recognised and
            # strict syntax checking is enabled
            if cmd in self.paramsDict:
                
                print "found: ", cmd,

                # There are 13 dictionary keys
                # Every single one will have a value tag
                
                # Get value attribute
                value = self.getAttrib(child, 'value')
                # Three will have a pixel tag
                # Get pixel if present..
                pixel = self.getAttrib(child, 'pixel')
                
                print "val,  %i pxl: %i" % (value, pixel)
                # Is pixel present?
                if pixel != -2:
                    print "pixel detected"
                    # pixel is defined; Updated dictionary key
                    self.setParamValue(cmd, pixel-1, value)
                else:
                    # pixel not present; of the remaining 10 keys 2 will have an index tag
                    index = self.getAttrib(theElement, 'index')
                    if index != -2:
                        print "index detected"
                        # update dictionary key value
                        self.setParamValue(cmd, index-1, value)
                    else:
                        # Neither a pixel nor index defined; update value (integer)
                        self.setParamValue(cmd, index, value)
            else:
                if self.strict:
                    raise LpdCommandSequenceError('Illegal command %s specified' % (child.tag))
        
        # Dictionary now updated, check keys XX_default and if they are not -1 
        # then their corresponding keys should be updated with whatever value the XX_default key has
        for key in self.paramsDict:
            # Is this a _default key?
            if key.endswith("_default"):
                print "Found _default key: ", key, ", = ", 
                # has its value been changed from -1?
                keyValue = self.getParamValue(key)
                print keyValue
                if keyValue[2] > -1:
                    print " is greater than -1, updating corresponding key.."
                    # Derived corresponding key's name
                    pairedKey = key.replace("_default", "")
                    pairedKeyValue = self.getParamValue(pairedKey)
                    length = len(pairedKeyValue[2])
                    print "length: ", length
                    for idx in range(length):
#                        print "pairedKey, idx, keyValue = ", pairedKey, idx, keyValue[2]
                        self.setParamValue(pairedKey, idx, keyValue[2])
        
        # Back up one level in the tree              
        self.depth = self.depth - 1
        
        # Return the encoded sequence for this (partial) tree
        return encodedSequence
#        return localNopsSum, encodedSequence
 
    def buildBitstream(self):
        '''
        loop over dictionary keys and building the word bitstream programmatically
        '''
        
        
        """ Condense all of the following down into looping over dictionary keys and building the word bitstream programmatically """
        test = False
        if test:
            # Pack command into 32 bit words 
            #  
            if cmd == 'mux_decoder':
                # Get dictionary key values
                cmdParams = self.getParamValue(cmd)
                print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
                print "mux_decoder detected: ", cmdParams[0], cmdParams[1], " [",
                for idx in range(512):
                    if (idx < 5) | (idx > 506):
                        print cmdParams[2][idx],
                    elif idx == 500:
                        print ", .., ",
                print "]"
                # Find where in slow control bitstream the current section begins
                #    Note: variable pixel determines the offset on added on to position
                position = cmdParams[1]         # Redundant?
                scWordWidth = cmdParams[0]
                # Update this pixel...
                # Obtain the corresponding 32-bit word
                
                # Determine where within the current section of the slow control bitstream we are
                # Note pixel = 1-512, Python list = 0-511
                bitstreamPosition = (pixel-1) * scWordWidth
                # Determine which 32 bit word that is
                wordPosition = bitstreamPosition / 32
                print "encodedSequence[...] = [%X, %X, %X]" % (encodedSequence[0], encodedSequence[1], encodedSequence[2])
                print "wordPosition = ", wordPosition
                # Copy contents of 32-bit word
                thisWord = encodedSequence[wordPosition]
                # Determine offset inside 32 bit word
                indexOffset = bitstreamPosition % 32
                # Calculate bit mask to clear the bits corresponding to the width of the slow control word
                mask = (2**32-1) - (7 << indexOffset)
                print "indexOffset: ", indexOffset, " value: %X " % value, " -> ",
                # Move slow control word into its relative position within the 32-bit word
                scWord = value << indexOffset
                print " %X" % scWord
                print "bitstreamPosition: ", bitstreamPosition, " wordPosition: ", wordPosition
                print "123456789123456789123456789123456789"
                print "Before: %x %x %x" % (thisWord, mask, scWord)
                # Update 32-bit word with the individual slow control word in the correct position
                thisWord = thisWord & mask | scWord
                print "After:  %x %x %x" % (thisWord, mask, scWord)
                # Update encodedSequence
                encodedSequence[wordPosition] = thisWord
                 
                
            elif cmd == 'mux_decoder_default':
                # This is a default value, unless it is still -1 (not set)
                cmdParams = self.getParamValue(cmd)
                if cmdParams[2] == -1:
                    print "The value of key %s was not set." % cmdParams[0]
                    print "This should not be possible?"
                else:
                    # Default value set, update the mux decoder settings for the 512 pixels accordingly
                    # The default value is:
                    print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
#                        print type(cmdParams)
                    print "Key %s has value = " % cmd, cmdParams

                    # Obtain all the slow control values this section
                    # Start by deriving the section name from the default key name (remove '_default')
                    sectionName = cmd.replace("_default", "")
                    scSectionValues = self.getParamValue(sectionName)
                    
                    print "mux Section: ", scSectionValues[0], scSectionValues[1], " [",
                    for idx in range(512):
                        if (idx < 5) | (idx > 506):
                            print scSectionValues[2][idx],
                        elif idx == 500:
                            print ", .., ",
                    print "]"
                    
                    # Define variables used to process flow control words into 32 bit words
                    # Define slow control word width
                    scWordWidth = cmdParams[0]
                    # Track bit position relative to 32 bit word boundary (since 32 not evenly divisible by scWordWidth)
                    relativeBit = 0
                    # Save the contents of one 32 bit word
                    seqIndex = 0
                    # Save excess of any slow control word that spans the 32 bit word boundary
                    bitRemainder = 0
                    # Track relative position within the slow control bitstream
                    scBitTracker = 0
                    # Number of bit(s) before a 32 bit word boundary
                    endNumBits = 0
                    # Number of bit(s) after a 32 bit word boundary
                    startNumBits = 0
                    while scBitTracker < 1536:
                        # Calculate slow control word position relative to section
                        currentSlowCtrlWord = scBitTracker / scWordWidth
                        # Because we need to include the last bit of the section in order to save the very last 32 bit word, 
                        # the last value of variable currentSlowCtrlWord will become 1 bigger than the nested list of scSectionValues[2]

                        # Check that the current pixel has not been explicitly set already
                        # Obtain pixel value (-1 means that it has not been explicitly that already)
                        
                        if currentSlowCtrlWord == 512:
                            # currentSlowCtrlWord runs from 0-512; obviously 512 doesn't exist
                            # Increment loop counter and continue
                            print "Yes - I think that checking this value for 512 must be redundant..??"
                            scBitTracker += scWordWidth
                            continue
                            
                        currentPixelVal = scSectionValues[2][ currentSlowCtrlWord ]
                        # if it's -1, it's fine to overwrite the old value
                        if currentPixelVal == -1:
                            
                            # How far away from the 32-bit word boundary are we?
                            relativeBit = scBitTracker % 32
                            # If relativeBit > 29 (i.e. 30 or 31) then the current slow control word straddles the 32-bit word boundary 
                            if relativeBit > 29:
                                # Determine how many bits on each side of the boundary
                                endNumBits = 32 - relativeBit
                                startNumBits = scWordWidth - endNumBits

                                # Calculate how many LSB(s) to save (to the current 32-bit word)
                                bitMask = (2**endNumBits) - 1
                                # Save the LSB(s), discarding the MSB(s)
                                currentVal = cmdParams[2] & bitMask
                                # Bit shift by relativeBit and add to 32 bit word
                                seqIndex += currentVal << relativeBit
                                # Save the remaining MSB(s)
                                bitRemainder = cmdParams[2] >> endNumBits
                                # Save 32 bit word to sequence
                                encodedSequence[seqPosition] = seqIndex
                                seqPosition += 1
                                # Save remaining MSB(s) to the next 32 bit word
                                seqIndex = bitRemainder #endNumBits
                            else:
                                # Is this a 32 bit boundary (and not the very first loop iteration)?
                                if (relativeBit == 0) and (scBitTracker > 0):
                                    # Save 32 bit word to sequence
                                    encodedSequence[seqPosition] = seqIndex
                                    seqPosition += 1
                                    # Clear the 32 bit word before proceeding                                    
                                    seqIndex = 0

                                # Bit shift slow control word by relative position within 32-bit word
                                currentVal = cmdParams[2] << relativeBit
                                # Add the current scWordWidth bits long word to the 32-bit word
                                seqIndex += currentVal
                                
                            # Increment loop counter (by scWordWidth bits)
                            scBitTracker += scWordWidth
                        else:
                            # This pixel has already been set explicitly, do not overwrite
                            #    Note: pixel = 1-512, Python list = 0-511
                            print "Detected pixel no %i already set" % (currentSlowCtrlWord+1)
                            
                            ''' Note: Still need to save the 32 bit word if the slow control word is located at the word boundary '''
                            # 
                            # Increment loop counter (by scWordWidth bits)
                            scBitTracker += scWordWidth
        
#                        if (relativeBit == 0) and (scBitTracker > 0):
                    # Save the last 32 bit word to sequence
                    encodedSequence[seqPosition] = seqIndex
                    seqPosition += 1
 

    def displayDictionaryValues(self):
        '''
            Debug function, used to display the dictionary values
        '''
        
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
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <self_test_decoder_default value="7"/>
                                <mux_decoder_default value="3"/>
                                <daq_bias index="47" value="11"/>
                                <digital_control index="3" value="18"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        
        print "Before: "
        paramsObj.displayDictionaryValues()
        
        paramsObj.encode()
#        paramsObj.setParamValue(dictKey, index, value)
        paramsObj.displayDictionaryValues()
        newVals = paramsObj.getParamValue(dictKey)

        print newVals, expectedVals
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

        # Strictly not necessary except for the class constructor requiring a XML file or string
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
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
        
if __name__ == '__main__':
    
    
    # Execute unit testing
    unittest.main()
    
    sys.exit()
    ''' Manual testing '''
    theParams = SlowCtrlParams('sampleSlowControl.xml', fromFile=True)
#    theParams = SlowCtrlParams('simple.xml', fromFile=True)
    
#    theParams.getParamValue("mux_decoder_default")
    width, posn, val = theParams.getParamValue("mux_decoder_default")
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
