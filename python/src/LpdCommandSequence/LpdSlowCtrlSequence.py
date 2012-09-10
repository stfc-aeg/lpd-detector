'''
Created on Aug 22, 2012

A replica of LpdSlowCtrlSequenceParser - To investigate implementation of Slow Control using XML

@author: Christian Angelsen, STFC Application Engineering Group
'''

from xml.etree.ElementInclude import ElementTree
from xml.etree.ElementTree import ParseError

class LpdSlowCtrlSequence(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)
    
class LpdSlowCtrlSequenceParser():
   
    def __init__(self, xmlObject, fromFile=False, strict=True):

        # Set the strict syntax flag to specified value (defaults to true)
        self.strict = strict
        
        # Define slow control offsets
        muxOffset = 0x00
        # ..
        biasOffset = 3585
        
        # Dictionary of slow commands and their associated values
        self.cmdDict = { 'mux_decoder_default'          : 0x00,
                         'mux_decoder'                  : 0x01,
                         'feedback_select_default'      : 0x02,
                         'feedback_select'              : 0x03,
                         'self_test_decoder_default'    : 0x04,
                         'self_test_decoder'            : 0x05,
                         'self_test_enable'             : 0x06,
                         'daq_bias_default'             : 0x07,
                         'daq_bias'                     : 0x08,
                         'spare_bits'                   : 0x09,
                         '100x_filter_control'          : 0x0a,
                         'adc_clock_delay'              : 0x0b,
                         'digital_control'              : 0x0c,
                      }
        
        # Definition of position of fast command fields in BRAM words
        #TODO: There are no offsets in the slow control, therefore these five variables will become redundant:  ???
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
        if self.root.tag != 'lpd_slow_ctrl_sequence':
#        if self.root.tag != 'lpd_command_sequence':
            raise LpdSlowCtrlSequence('Root element is not an LPD Slow Control command sequence')

    def encode(self):
        #TODO: Update Comment
        '''
        Encodes the command sequence into the packed binary values needed for the
        FEM BRAM structure, which is returned as a list of integers. 
        '''
        
        # Intialise tree depth (used for debugging only)
        self.depth = 0
        
        # Parse the tree, starting at the root element, obtaining the packed
        # binary command sequence as a list
        self.total_number_nops, sequence  = self.parseElement(self.root)
        
        # Count the total number of words
        self.total_number_words = len(sequence)
        
        # Return the command sequence
        return sequence
        
    def parseElement(self, theElement):
        '''
        Parses an element (partial tree) of the XML command sequence, encoding commands
        into the appropriate values and returning them. Is called recursively to traverse
        a tree structure of arbitrary depth, allowing nesting of loops etc
        '''
    
        # Initialise empty list to contain binary command values for this part of the tree
#        encodedSequence = []
        encodedSequence = [0L] * 261    # 261 because that's what the Matlab code is producing..
        
        # Track number of nops counted locally
        localNopsSum = 0
        
        # Increment tree depth counter
        self.depth = self.depth + 1
        
        # Loop over child nodes of the current element
        for child in theElement:

            # Get the command name (tag) for the current element
            cmd = child.tag
            
            # If this is a loop command, extract the number of loops from the count
            # attribute and then recursively call this function to encode the contents
            # of the loop. A loop command _must_ contain commands, otherwise raise an
            # exception
            if cmd == 'loop':
                
                #TODO: No need for a loop in the slow control
                pass
                
#                numLoops = self.getCountAttrib(child)
#                
#                if len(child):
#                    nopsSum, childSequence = self.parseElement(child) 
#                    localNopsSum += nopsSum * numLoops 
#                    encodedSequence.extend(childSequence * numLoops)
#                else:
#                    raise LpdSlowCtrlSequence('Loop specified with no children')
                
            else:
                
                # Otherwise, check this command is in the syntax dictionary and process
                # accordingly. Raise an exception if the command is not recognised and
                # strict syntax checking is enabled
                if cmd in self.cmdDict:
                
                    # Get count and NOP attributes    
                    count = self.getCountAttrib(child)
                    #TODO: nops likely to become redundant?
                    nops  = self.getNopAttrib(child)
                    
                    
                    #TODO: if mux_decoder_pixel_master defined, clear all the mux_decoder_pixel_ stop processing
                    #    and stop processing for any future mux_decoder_pixel_.. variables
                    
                    #TODO: sync_reset not used in Slow Control
                    
                    # Pack command and number of NOPs into binary word with sync bits etc. sync_reset
                    # commands are treated as a special case and packed differently. 
#                    if cmd == 'sync_reset':
#                        cmdWord = (self.cmdDict[cmd] << self.sync_reset_pos)
#                    else:
#                        cmdWord = (self.sync << self.sync_pos) | (self.cmdDict[cmd] << self.cmd_pos)
#   
                    # 
                    dictValue = self.cmdDict[cmd]
                    # Bit Shift according to number of bits within the targeted word (1 word is 32 bits)
                    wordOffset = dictValue % 32
                    # Offset variable count by wordOffset within the 32-bit word
                    cmdWord = (count << wordOffset)
                    # Calculator where in list this word belongs
                    listOffset = dictValue / 32
                    
                    #TODO: No need for nop in Slow Control ?
                    
#                    # Add in the NOPs to the command word. If the command itself is a NOP, use
#                    # the count attribute to specify how many NOPs to add. Also reset count to
#                    # 1 to avoid injecting repeated individual NOPs into the encoded sequence
#                    if cmd == 'nop':
#                        #TODO: Eliminate nop if proven redundant? (replace with pass statement)
#                        if nops > 0:
#                            raise LpdSlowCtrlSequence('NOPs atttribute specified for NOP command, use count attribute instead')
#                        
#                        cmdWord = (count - 1 << self.nop_pos) | cmdWord
#                        # Count number of nops
#                        localNopsSum += count
#                        count = 1
#                        
#                    else:
#                        cmdWord = (nops << self.nop_pos) | cmdWord
#                        # Count number of nops if specified
#                        if nops > 0:
#                            localNopsSum += nops

                    
                    # Append packed command word to the encoded sequence the number of times
                    # specified by the count attribute
                    #encodedSequence.extend([cmdWord] * count)
                    
                    # Or existing value with new value..
                    existingValue = encodedSequence[listOffset]
                    cmdWord = existingValue | cmdWord
                    encodedSequence[listOffset] = cmdWord
                                                                
                else:
                    if self.strict:
                        raise LpdSlowCtrlSequence('Illegal command %s specified' % (child.tag))
      
        # Back up one level in the tree              
        self.depth = self.depth - 1
        
        # Return the encoded sequence for this (partial) tree
        return localNopsSum, encodedSequence
    
    #TODO: Remove if nop proven redundant
    def getTotalNumberNops(self):
        '''
        Returns the total number of nops read
        '''
        
        return self.total_number_nops
    
    def getTotalNumberWords(self):
        '''
        Returns the total number of words
        '''
        
        return self.total_number_words
        
    def getCountAttrib(self, theElement):
        '''
        Returns the value of the count attribute of the specified element if it exists,
        or a default value of 1 if not. Can also throw an exception if a non-integer
        count attribute is detected
        '''

        # Get the count attribute or a default value of 1
        countAttrib = theElement.get('count', default='1')
        
        # Convert count to integer or raise an exception if this failed
        try:
            count = int(countAttrib)
        except ValueError:
            raise LpdSlowCtrlSequence('Non-integer count attribute specified')
        
        # Return integer count value    
        return count
    
    #TODO: Remove if nop is proven redundant
    def getNopAttrib(self, theElement):
        '''
        Returns the value of the NOP attribute of the specified element if it exists,
        or a default value of 0 if not, Can also thrown an exception if a non-integer
        nop attribute is detected
        '''
        
        nopAttrib = theElement.get('nop', default='0')
        try:
            nop = int(nopAttrib)
        except ValueError:
            raise LpdSlowCtrlSequence('Non-integer nop attribute specified')
        
        return nop
    
import unittest
    
class LpdSlowCtrlSequenceParserTest(unittest.TestCase):
    '''
    Unit test class for LpdSlowCtrlSequenceParser.
    '''
    
#    def testStringParse(self):
#        '''
#        Tests that parsing a command sequence specified as a string argument
#        returns an encoded sequence that is expected
#        '''
#
#        # Command sequence definition to encode
#        stringCmdXml = '''<?xml version="1.0"?>
#                            <lpd_command_sequence name="TestString">
#                                <sync_reset/>
#                                <stand_by nop="3"/>
#                                <loop count="2">
#                                    <reset_trigger_pointer/>
#                                    <clear_skip_register/>
#                                </loop>
#                            </lpd_command_sequence>
#        '''
#        # Expected encoded values
#        expectedSeq = [0x169694, 0xe01000, 0x20d000, 0x20b000, 0x20d000, 0x20b000]
#        
#        # Parse XML and encode
#        stringCmdSeq = LpdSlowCtrlSequenceParser(stringCmdXml)
#        stringEncodedSeq = stringCmdSeq.encode()
#
#        # Test that encoded sequence matches expected
#        self.assertEqual(stringEncodedSeq, expectedSeq, 'Unexpected encoded result for string command sequence')
        
    def testFileParse(self):

        expectedLenEncoded = 25
        
        fileCmdSeq = LpdSlowCtrlSequenceParser('slowCtrlTest.xml', fromFile=True)
        fileEncodedSeq = fileCmdSeq.encode()

        self.assertEqual(len(fileEncodedSeq), expectedLenEncoded, 
                         'Mismatch in encoded length: got %d expected %d' % (len(fileEncodedSeq), expectedLenEncoded))
        
#    def testLoopException(self):
#
#        stringCmdXml = '''<?xml version="1.0"?>
#                            <lpd_command_sequence name="LoopException">
#                                <sync_reset/>
#                                <stand_by nop="3"/>
#                                <loop count="wibble">
#                                    <reset_trigger_pointer/>
#                                    <clear_skip_register/>
#                                </loop>
#                            </lpd_command_sequence>   
#                        '''
#        stringCmdSeq = LpdSlowCtrlSequenceParser(stringCmdXml)
#        with self.assertRaises(LpdSlowCtrlSequence):
#            stringCmdSeq.encode()
            
#    def testIllegalRootTag(self):
#        
#        stringCmdXml = '''<?xml version="1.0"?>
#                            <not_a_lpd_command_sequence name="IllegalRootTag">
#                                <sync_reset/>
#                                <stand_by nop="3"/>
#                                <loop count="2">
#                                    <reset_trigger_pointer/>
#                                    <clear_skip_register/>
#                                </loop>
#                            </not_a_lpd_command_sequence>   
#                        '''
#        with self.assertRaises(LpdSlowCtrlSequence):
#            LpdSlowCtrlSequenceParser(stringCmdXml)
            
        
if __name__ == '__main__':
         
    unittest.main()
            
