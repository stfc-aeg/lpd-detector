'''
    Author: ckd27546
    
    Created: 18 April 2013
'''

import argparse

class FilterCtrlDecode():

    def __init__(self, TagValue):
        '''
        FilterCtrlDecode accepts a <filter_control>'s value and decodes it into it's constituent Reserved and FilterEnable parts.
        e.g:
        <filter_control value="18275"/> 
        would be broken down to:
        Reserved = 9137
        FilterEnable = 1
        '''
        if Debug:
            print "\nThe tag value's binary value is: %s" % self.displayBinaryString(TagValue)

        Reserved = (TagValue >> 1)
        FilterEnable = (TagValue & 0x1)

        print "Reserved:     %6i" % Reserved
        print "FilterEnable: %6i" % FilterEnable

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
    parser = argparse.ArgumentParser(description="FilterCtrlDecode.py - accepts the value of a <filter_control> XML tag and displays it's two constituent parts' equivalent values.",
                                     epilog="Example usage: python FilterCtrlDecode.py --tagvalue 5406687746")

    parser.add_argument("--tagvalue", help="the value of the XML tag", type=int)
    parser.add_argument("--debug", help="set debug to 1 for debug information", type=int, choices=[0, 1])
    args = parser.parse_args()

    if args.tagvalue:
        TagValue = args.tagvalue
    if args.debug:
        Debug = args.debug
    thisObj = FilterCtrlDecode(TagValue)

