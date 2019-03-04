'''
    Author: ckd27546
    
    Created: 18 April 2013
'''

import argparse

class DigitalCtrlDecode():

    def __init__(self, TagValue):
        '''
        DigitalCtrlDecode accepts a <digital_control>'s value and decodes it into it's constituent Reserved, Reset3, Reset2, Reset1, ClockCounterOffset and ClockSelect parts.
        e.g:
        <digital_control value="5406687746"/> 
        would be broken down to:
        Reserved = 0 
        Reset3   = 10
        reset2   = 9 
        Reset1   = 7
        Clockcounteroffset = 2 
        Clockselect 2
        '''
        if Debug:
            print "\nThe tag value's binary value is: %s" % self.displayBinaryString(TagValue)

        ClockSelect = (TagValue & 0xFF)
        bitPosition = 8
        ClockCounterOffset = ( (TagValue >> bitPosition) & 0x7F)
        bitPosition += 7
        Reset1 = ( (TagValue >> bitPosition) & 0x7F)
        bitPosition += 7
        Reset2 = ( (TagValue >> bitPosition) & 0x7F)
        bitPosition += 7
        Reset3 = ( (TagValue >> bitPosition) & 0x7F)
        bitPosition += 7
        Reserved = ( (TagValue >> bitPosition) & 0xF)

        print "Reserved:           %3i" % Reserved
        print "Reset3:             %3i" % Reset3
        print "Reset2:             %3i" % Reset2
        print "Reset1:             %3i" % Reset1
        print "ClockCounterOffset: %3i" % ClockCounterOffset
        print "ClockSelect:        %3i" % ClockSelect

    def displayBinaryString(self, decValue):
        '''
            Turns the value of argument 'decValue' into a string, organising the bits into groups of four
        '''
        # Turn value into binary string
        strValue = bin(decValue)
        # Split the binary string into groups of four bits (in reverse order)
        reversedGroupedBitsString = ""
        for i in range(1, len(strValue)+1):
            reversedGroupedBitsString += strValue[-i]
            if i % 4 == 0:
                reversedGroupedBitsString += " "
        
        # Reversed the order
        correctOrder = ""
        for i in range(len(reversedGroupedBitsString)-1,-1,-1):
            correctOrder += reversedGroupedBitsString[i]
        return correctOrder

if __name__ == '__main__':
    
    TagValue = 0
    Debug = 0
    
    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="DigitalCtrlDecode.py - accepts the value of a <digital_control> XML tag and displays it's six constituent parts' equivalent values.",
                                     epilog="Example usage: python DigitalCtrlDecode.py --tagvalue 5406687746")

    parser.add_argument("--tagvalue", help="the value of the XML tag", type=int)
    parser.add_argument("--debug", help="set debug to 1 for debug information", type=int, choices=[0, 1])
    args = parser.parse_args()

    if args.tagvalue:
        TagValue = args.tagvalue
    if args.debug:
        Debug = args.debug
    thisObj = DigitalCtrlDecode(TagValue)
