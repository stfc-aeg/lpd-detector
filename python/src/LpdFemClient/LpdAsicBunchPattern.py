'''
Created on 20 Apr 2012

@author: Tim Nicholls, STFC Application Engineering Group
'''

from xml.etree.ElementInclude import ElementTree
from xml.etree.ElementTree import ParseError

class LpdAsicBunchPatternError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)
    
class LpdAsicBunchPattern():
   
    def __init__(self, xmlObject, fromFile=False, strict=True): #, cccEnabled=False):

        # Set the strict syntax flag to specified value (defaults to true)
        self.strict = strict
        
        # Dictionary of fast commands and their associated values
        self.cmdDict = { 'veto'                      : 0x00}

        # Parse the XML specified, either from a file if the fromFile flag
        # was set or from the string passed
        if fromFile == True:
            self.tree = ElementTree.parse(xmlObject)
            self.root = self.tree.getroot()
        else:
            self.tree = None 
            self.root = ElementTree.fromstring(xmlObject)

        # Get the root of the tree and verify it is an lpd_bunch_pattern
        if self.root.tag != 'lpd_bunch_pattern':
            raise LpdAsicBunchPatternError('Root element is not an LPD bunch pattern')

        self.bDebug = False

    def encode(self):
        '''
        Encodes the command sequence into the packed binary values needed for the
        FEM BRAM structure, which is returned as a list of integers. 
        '''
        
        # Parse the tree, starting at the root element, obtaining the packed
        # binary command sequence as a list
        sequence  = self.parseElement(self.root)
        
        # Return the command sequence
        return sequence
        
    def parseElement(self, theElement):
        '''
        Parses an element (partial tree) of the XML values
        into the appropriate pattern(s)' word(s) and returns them.
        '''

        # Initialise empty list to contain 96 (32-bit) words * 10 patterns
        encodedSequence = [0] * 96 * 10
        
        # Loop over child nodes of the current element
        for child in theElement:

            # Get the command name (tag) for the current element
            cmd = child.tag
            
            # Put value into pattern/word as specified. Omitting word will fill all words
            # within same pattern, omitting pattern will fill specified word across all 
            # patterns. Omitting both pattern and word will set all words in all patterns.
            # 
            # Note that the XML is passed in the order of the file, so the convention is to
            # set values across multiple patterns/words, and then set specific words
            
            if cmd in self.cmdDict:
            
                # Get count and NOP attributes    
                pattern = self.getPatternAttrib(child, 'pattern')
                word    = self.getPatternAttrib(child, 'word')
                value   = self.getPatternAttrib(child, 'value')
                
                if value == -1:
                    raise LpdAsicBunchPatternError('Error XML tag %s missing value attribute' % cmd)
#                else:
#                    print "%s, pattern = %d, word = %d, value = %d" % (cmd, pattern, word, value)
                
                if pattern != -1:
                    # pattern specified
                    if word != -1:
                        # Both pattern and word specified
                        index = (pattern * 96) + (word)
                        encodedSequence[index] = value
                    else:
                        # word not specified: Update all words within pattern
                        for word in range(96):
                            index = (pattern * 96) + (word)
                            encodedSequence[index] = value                            
                else:
                    # pattern not specified 
                    if word != -1:
                        # Not pattern, but word specified
                        for pattern in range(10):
                            index = (pattern * 96) + (word)
                            encodedSequence[index] = value
                    else:
                        # Neither pattern, word specified: Update a lot
                        for pattern in range(10):
                            for word in range(96):
                                index = (pattern * 96) + (word)
                                encodedSequence[index] = value                            
            else:
                if self.strict:
                    raise LpdAsicBunchPatternError('Illegal command %s specified' % (child.tag))
        
        # Return the encoded sequence for this (partial) tree
        return encodedSequence

        
    def getPatternAttrib(self, theElement, attribute):
        '''
        Returns the value of the "attribute" of the specified element if it exists,
        or a default value of -1 if not. Can also throw an exception if a non-integer
        count attribute is detected
        '''

        # Get the count attribute or a default value of -1
        countAttrib = theElement.get(attribute, default='-1')
        
        if self.bDebug: print "getPatternAttrib() ", countAttrib, type(countAttrib), " attribute = ", attribute
        
        # Convert count to integer or raise an exception if this failed
        try:
            count = int(countAttrib)
        except ValueError:
            # Try again using base 16 ('value' = hexadecimal)
            try:
                count = int(countAttrib, 16)
            except ValueError:
                raise LpdAsicBunchPatternError('Non-integer %s attribute specified' % attribute)
        
        # Return integer count value    
        return count

    
import unittest
    
class LpdAsicCommandSequenceTest(unittest.TestCase):
    '''
    Unit test class for LpdAsicBunchPattern.
    '''
    
    def testValueException(self):
        '''
        Should fail if value not specified in XML tag
        '''
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_bunch_pattern name="testValueRaisesError">
                                <veto pattern="0" word="0" />
                            </lpd_bunch_pattern>
        '''

        stringCmdSeq = LpdAsicBunchPattern(stringCmdXml)
        with self.assertRaises(LpdAsicBunchPatternError):
            stringCmdSeq.encode()

    def testCCC_xml(self):
        '''
            Sanity check..
        '''

        # Command sequence definition to encode
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_bunch_pattern name="testCCC_xml">
                                <veto pattern="3"          value="0x30"/>
                                <veto             word="1" value="0x20"/>
                                <veto pattern="0" word="0" value="0x10"/>
                            </lpd_bunch_pattern>
        '''

        # Parse XML and encode
        stringCmdSeq = LpdAsicBunchPattern(stringCmdXml)
        stringEncodedSeq = stringCmdSeq.encode()
        
        expectedSeq = [0] * 960
        expectedSeq[0] = 16
        for index in range(96*3, 96*4, 1):
            expectedSeq[index] = 48
        for index in range(1, 960, 96):
            expectedSeq[index] = 32

        self.assertEqual(stringEncodedSeq, expectedSeq, "Mismatch between encoded and expected strings")


    def test_FillingAllWords(self):
        '''
            Sanity check..
        '''

        # Command sequence definition to encode
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_bunch_pattern name="test_FillingAllWords">
                                <veto   value="0xF0F0F0F0"/>
                            </lpd_bunch_pattern>
        '''

        # Parse XML and encode
        stringCmdSeq = LpdAsicBunchPattern(stringCmdXml)
        stringEncodedSeq = stringCmdSeq.encode()
        
        expectedSeq = [0xF0F0F0F0] * 960

        self.assertEqual(stringEncodedSeq, expectedSeq, "Mismatch between encoded and expected strings")

    def test_file(self):
        '''
            Test parsing XML file
        '''
        fileCmdSeq = LpdAsicBunchPattern("/u/ckd27546/workspace/lpdSoftware/LpdFemClient/tests/veto_file_test.xml", fromFile=True)
        fileEncodedSeq = fileCmdSeq.encode()

if __name__ == '__main__':
         
    unittest.main()
