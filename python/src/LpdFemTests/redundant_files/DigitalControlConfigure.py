'''
    Author: ckd27546
    
    Created: 14 November 2012
'''

import argparse

class DigitalControlConfigure():

    def __init__(self, Reserved=0, Reset3=10, Reset2=9, Reset1=7, ClockCounterOffset=2, ClockSelect=2, Debug=0):
        '''
            DigitalControlConfigure allows the user to specify up to all six of the different parts of the Digital Control Slow Control Section
        '''
                
        # Bit Position within Digital Control section
        bitPosition = 0
        
        # ClockSelect bits 32-39
        ClockSelect = ClockSelect << bitPosition
        bitPosition += 8

        # ClockCounterOffset bits 25-31
        ClockCounterOffset = ClockCounterOffset << bitPosition
        bitPosition += 7

        # Reset1 occupies bits 18-24
        Reset1 = Reset1 << bitPosition
        bitPosition += 7

        # Reset2 occupies bits 11-17
        Reset2 = Reset2 << bitPosition
        bitPosition += 7

        # Reset3 occupies the following seven bits (4-10)
        Reset3 = Reset3 << bitPosition
        bitPosition += 7

        # Reserved occupies the first four bits (0-3)
        Reserved = Reserved << bitPosition

        total = Reserved + Reset3 + Reset2 + Reset1 + ClockCounterOffset + ClockSelect
        
        # Construct digital_control XML tag
        xmlTag = """<digital_control value="%i"/>""" % total

        print "\nGenerated Digital Control XML tag: \t\t", xmlTag, "\n"

        if Debug:
            print "And its binary value is: %s\n" % self.displayBinaryString(total)

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

if __name__ == "__main__":

    # Example usage:
    '''
        python DigitalControlConfigure.py --reserved 0 --reset3 10 --reset2 9 --reset1 7 --clockcounteroffset 2 --clockselect 2
    '''

    # Debug variable
    Debug = 0
        
    # Define class arguments
    Reserved    = 0
    Reset3      = 0
    Reset2      = 0
    Reset1      = 0
    ClockCounterOffset = 0
    ClockSelect = 0
    
    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="DigitalControlConfigure.py - Accepts up to 6 arguments to set the functions compromising the Digital Control keyword and generates the 40 bit word used by the <digital_control> XML tag. ",
                                     epilog="The perceived wisdom is that the following function values are the default settings:\nreserved = 0\nreset3 = 10\nreset2 = 9\nreset1 = 7\nclockcounteroffset = 2\nclockselect = 2,\t Note: the parser ignores any argument set to 0 and therefore the default value is 0 for any of the six arguments if not provided.")

    parser.add_argument("--reserved", help="set the Reserved function (4 bits)", type=int)
    parser.add_argument("--reset3", help="set the Reset3 function (7 bits)", type=int)
    parser.add_argument("--reset2", help="set the Reset2 function (7 bits)", type=int)
    parser.add_argument("--reset1", help="set the Reset1 function (7 bits)", type=int)
    parser.add_argument("--clockcounteroffset", help="set the Clock Counter Offset function (7 bits)", type=int)
    parser.add_argument("--clockselect", help="set the Clock Select function (8 bits)", type=int)
    parser.add_argument("--debug", help="set debug to 1 for debug information", type=int)
    args = parser.parse_args()

    # Copy value(s) for the provided arguments
    if args.reserved:
        Reserved = args.reserved
    if args.reset3:
        Reset3 = args.reset3
    if args.reset2:
        Reset2 = args.reset2
    if args.reset1:
        Reset1 = args.reset1
    if args.clockcounteroffset:
        ClockCounterOffset = args.clockcounteroffset
    if args.clockselect:
        ClockSelect = args.clockselect
    if args.debug:
        Debug = args.debug

    DigitalControlConfigure(Reserved, Reset3, Reset2, Reset1, ClockCounterOffset, ClockSelect, Debug)
    
    
