'''
Created on 20 Apr 2012

@author: Tim Nicholls, STFC Application Engineering Group
'''

from xml.etree.ElementInclude import ElementTree
from xml.etree.ElementTree import ParseError

class LpdCommandSequenceError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)
    
class LpdCommandSequenceParser():
   
    def __init__(self, xmlObject, fromFile=False, strict=True):

        # Set the strict syntax flag to specified value (defaults to true)
        self.strict = strict
        
        # Dictionary of fast commands and their associated values
        self.cmdDict = { 'nop'                      : 0x00, 
                         'stand_by'                 : 0x01, 
                         'power_up'                 : 0x02,
                         'on_chip_reset_disable'    : 0x03,
                         'on_chip_reset_enable'     : 0x04,
                         'reset_pre_amp'            : 0x05,
                         'reset_gain_front'         : 0x06,
                         'reset_gain_back'          : 0x07,
                         'test_mode_d'              : 0x09,
                         'tune_mode'                : 0x0a,
                         'clear_skip_register'      : 0x0b,
                         'reset_write_pointer'      : 0x0c,
                         'reset_trigger_pointer'    : 0x0d,
                         'start_write_pointer'      : 0x0e,
                         'start_trigger_pointer'    : 0x0f,
                         'trigger_flag_set'         : 0x10,
                         'read_out_data'            : 0x11,
                         'remove_reset_pre_amp'     : 0x12,
                         'remove_reset_gain_stage1' : 0x13,
                         'remove_reset_gain_stage2' : 0x14,
                         'clock_div_sel'            : 0x15,
                         'self_test_en'             : 0x16,
                         'stop_read_out'            : 0x17,
                         'reset_state_machine'      : 0x18,
                         'sync_reset'               : 0x5a5a5
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

    def encode(self):
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
        encodedSequence = []
        
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
                
                numLoops = self.getCountAttrib(child)
                
                if len(child):
                    nopsSum, childSequence = self.parseElement(child) 
                    localNopsSum += nopsSum * numLoops 
                    encodedSequence.extend(childSequence * numLoops)
                else:
                    raise LpdCommandSequenceError('Loop specified with no children')
                
            else:
                
                # Otherwise, check this command is in the syntax dictionary and process
                # accordingly. Raise an exception if the command is not recognised and
                # strict syntax checking is enabled
                if cmd in self.cmdDict:
                
                    # Get count and NOP attributes    
                    count = self.getCountAttrib(child)
                    nops  = self.getNopAttrib(child)
                    
                    # Pack command and number of NOPs into binary word with sync bits etc. sync_reset
                    # commands are treated as a special case and packed differently. 
                    if cmd == 'sync_reset':
                        cmdWord = (self.cmdDict[cmd] << self.sync_reset_pos)
                    else:
                        cmdWord = (self.sync << self.sync_pos) | (self.cmdDict[cmd] << self.cmd_pos)
   
                        
                    # Add in the NOPs to the command word. If the command itself is a NOP, use
                    # the count attribute to specify how many NOPs to add. Also reset count to
                    # 1 to avoid injecting repeated individual NOPs into the encoded sequence
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
            raise LpdCommandSequenceError('Non-integer count attribute specified')
        
        # Return integer count value    
        return count
    
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
            raise LpdCommandSequenceError('Non-integer nop attribute specified')
        
        return nop
    
import unittest
    
class LpdCommandSequenceParserTest(unittest.TestCase):
    '''
    Unit test class for LpdCommandSequenceParser.
    '''
    
    def testStringParse(self):
        '''
        Tests that parsing a command sequence specified as a string argument
        returns an encoded sequence that is expected
        '''

        # Command sequence definition to encode
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_command_sequence name="TestString">
                                <sync_reset/>
                                <stand_by nop="3"/>
                                <loop count="2">
                                    <reset_trigger_pointer/>
                                    <clear_skip_register/>
                                </loop>
                            </lpd_command_sequence>
        '''
        # Expected encoded values
        expectedSeq = [0x169694, 0xe01000, 0x20d000, 0x20b000, 0x20d000, 0x20b000]
        
        # Parse XML and encode
        stringCmdSeq = LpdCommandSequenceParser(stringCmdXml)
        stringEncodedSeq = stringCmdSeq.encode()

        # Test that encoded sequence matches expected
        self.assertEqual(stringEncodedSeq, expectedSeq, 'Unexpected encoded result for string command sequence')
        
    def testFileParse(self):

        expectedLenEncoded = 25
        
        fileCmdSeq = LpdCommandSequenceParser('adcSweep.xml', fromFile=True)
        fileEncodedSeq = fileCmdSeq.encode()

        self.assertEqual(len(fileEncodedSeq), expectedLenEncoded, 
                         'Mismatch in encoded length: got %d expected %d' % (len(fileEncodedSeq), expectedLenEncoded))
        
    def testLoopException(self):

        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_command_sequence name="LoopException">
                                <sync_reset/>
                                <stand_by nop="3"/>
                                <loop count="wibble">
                                    <reset_trigger_pointer/>
                                    <clear_skip_register/>
                                </loop>
                            </lpd_command_sequence>   
                        '''
        stringCmdSeq = LpdCommandSequenceParser(stringCmdXml)
        with self.assertRaises(LpdCommandSequenceError):
            stringCmdSeq.encode()
            
    def testIllegalRootTag(self):
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <not_a_lpd_command_sequence name="IllegalRootTag">
                                <sync_reset/>
                                <stand_by nop="3"/>
                                <loop count="2">
                                    <reset_trigger_pointer/>
                                    <clear_skip_register/>
                                </loop>
                            </not_a_lpd_command_sequence>   
                        '''
        with self.assertRaises(LpdCommandSequenceError):
            LpdCommandSequenceParser(stringCmdXml)
            
        
if __name__ == '__main__':
         
    unittest.main()
            
