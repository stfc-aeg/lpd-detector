'''
    Author: ckd27546
    
    Created: 14 November 2012
'''

import argparse

class DigitalControlConfigure():

    def __init__(self, Reserved=0, Reset3= 0, Reset2=0, Reset1=0, ClockCounterOffset=0, ClockSelect=0):
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
    
if __name__ == "__main__":

    # Example usage:
    '''
        python LpdFemTests/redundant_files/DigitalControlConfigure.py --reserved 0 --reset3 0 --reset2 18 --reset1 14 --clockcounteroffset 14 --clockselect 4
    '''
    
    # Define class arguments
    Reserved    = 0
    Reset3      = 0
    Reset2      = 0 #18
    Reset1      = 0 #14
    ClockCounterOffset = 0  #14
    ClockSelect = 0 #4
    
    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="DigitalControlConfigure.py - Accepts up to 6 arguments to set the functions compromising the Digital Control keyword and generates the 40 bit word used by the <digital_control> XML tag. ",
                                     epilog="The perceived wisdom is that the following function values are the default settings:\nreserved = 0\nreset3 = 0\nreset2 = 18\nreset1 = 14\nclockcounteroffset = 14\nclockselect = 4,\t Note: the parser ignores any argument set to 0 and therefore the default value is 0 for any of the six arguments if not provided.")

    parser.add_argument("--reserved", help="set the Reserved function (4 bits)", type=int)
    parser.add_argument("--reset3", help="set the Reset3 function (7 bits)", type=int)
    parser.add_argument("--reset2", help="set the Reset2 function (7 bits)", type=int)
    parser.add_argument("--reset1", help="set the Reset1 function (7 bits)", type=int)
    parser.add_argument("--clockcounteroffset", help="set the Clock Counter Offset function (7 bits)", type=int)
    parser.add_argument("--clockselect", help="set the Clock Select function (8 bits)", type=int)
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


    DigitalControlConfigure(Reserved, Reset3, Reset2, Reset1, ClockCounterOffset, ClockSelect)
    
    