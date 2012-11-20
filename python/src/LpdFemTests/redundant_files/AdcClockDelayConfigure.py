'''
    Author: ckd27546
    
    Created: 19 November 12
'''

import argparse

class AdcClockDelayConfigure():

    def __init__(self, Reserved=0, DelayAdjust=0):
        '''
            AdcClockDelayConfigure allows the user to specify up to all two of the different parts of the Filter Control Slow Control Section
        '''
                
        # Bit Position within Filter Control section
        bitPosition = 0
        
        # DelayAdjust occupies bits 17-19
        DelayAdjust = DelayAdjust << bitPosition
        bitPosition += 3

        # Reserved occupies the first seventeen bits (0-16)
        Reserved = Reserved << bitPosition

        total = Reserved + DelayAdjust
        
        # Construct adc_clock_delay XML tag
        xmlTag = """<adc_clock_delay value="%i"/>""" % total

        print "\nGenerated ADC Clock Adjust Delay XML tag: \t\t", xmlTag, "\n"

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
        python LpdFemTests/redundant_files/AdcClockDelayConfigure.py --reserved 0 --delayadjust 0
    '''

    # Debug variable
    Debug = 0
        
    # Define class arguments
    Reserved    = 0
    DelayAdjust = 0
    
    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="AdcClockDelayConfigure.py - Accepts up to 2 arguments to set the functions compromising the Filter Control keyword and generates the 20 bit word used by the <adc_clock_delay> XML tag. ",
                                     epilog="The perceived wisdom is that the following function values are the default settings:\nreserved = 0\ndelayadjust = 0,\t Note: the parser ignores any argument set to 0 and therefore the default values of all of the two arguments is 0 if not provided.\t\t\t NOTE: SCRIPT NOT TESTED !")

    parser.add_argument("--reserved", help="set the Reserved function (17 bits)", type=int)
    parser.add_argument("--delayadjust", help="set the Delay Adjust function (3 bit)", type=int)
    parser.add_argument("--debug", help="set debug to 1 for debug information", type=int)
    args = parser.parse_args()

    # Copy value(s) for the provided arguments
    if args.reserved:
        Reserved = args.reserved
    if args.delayadjust:
        DelayAdjust = args.delayadjust
    if args.debug:
        Debug = args.debug

#    print "Reserved, DelayAdjust = ", Reserved, DelayAdjust
    AdcClockDelayConfigure(Reserved, DelayAdjust)
    
    