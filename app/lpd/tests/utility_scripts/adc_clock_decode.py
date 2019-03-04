'''
    Author: ckd27546
    
    Created: 18 April 2013
'''

import argparse

class AdcClockDecode():

    def __init__(self, TagValue):
        '''
        AdcClockDecode accepts a <adc_clock_delay>'s value and decodes it into it's constituent DelayAdjust and Reserved parts.
        e.g:
        <adc_clock_delay value="4"/> 
        would be broken down to:
        Reserved = 0
        DelayAdjust = 4
        '''
        if Debug:
            print "\nThe tag value's binary value is: %s" % self.displayBinaryString(TagValue)

        Reserved = TagValue >> 3
        AdcDelay = TagValue & 0x7
        print "Reserved: %8i" % Reserved
        print "AdcDelay: %8i\n" % AdcDelay

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
    parser = argparse.ArgumentParser(description="AdcClockDecode.py - accepts the value of a <adc_clock_delay> XML tag and displays it's two constituent parts' equivalent values.",
                                     epilog="Example usage: python AdcClockDecode.py --tagvalue 4")

    parser.add_argument("--tagvalue", help="the value of the XML tag", type=int)
    parser.add_argument("--debug", help="set debug to 1 for debug information", type=int, choices=[0, 1])
    args = parser.parse_args()

    if args.tagvalue:
        TagValue = args.tagvalue
    if args.debug:
        Debug = args.debug
    thisObj = AdcClockDecode(TagValue)
