'''
    Author: ckd27546
    
    Created: 19 November 12
'''

import argparse

class FilterControlConfigure():

    def __init__(self, Reserved=0, FilterEnable=0):
        '''
            FilterControlConfigure allows the user to specify up to all two of the different parts of the Filter Control Slow Control Section
        '''
                 
        # Bit Position within Filter Control section
        bitPosition = 0
        
        # FilterEnable occupies bit 19
        FilterEnable = FilterEnable << bitPosition
        bitPosition += 1

        # Reserved occupies the first eighteen bits (0-18)
        Reserved = Reserved << bitPosition

        total = Reserved + FilterEnable
        
        # Construct filter_control XML tag
        xmlTag = """<filter_control value="%i"/>""" % total

        print "\nGenerated Filter Control XML tag: \t\t", xmlTag, "\n"

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
        python FilterControlConfigure.py --reserved 0 --filterenable 1
    '''
    # Debug variable
    Debug = 0
        
    # Define class arguments
    Reserved    = 0 
    FilterEnable = 0
    
    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="FilterControlConfigure.py - Accepts up to 2 arguments to set the functions compromising the Filter Control keyword and generates the 20 bit word used by the <filter_control> XML tag. ",
                                     epilog="The perceived wisdom is that the following function values are the default settings:\nreserved = 0\nfilterenable = 1,\t Note: the parser ignores any argument set to 0 and therefore the default values of both of the two arguments are 0 if not provided.")

    parser.add_argument("--reserved", help="set the Reserved function (19 bits)", type=int)
    parser.add_argument("--filterenable", help="set the Filter Enable function (1 bit)", type=int)
    parser.add_argument("--debug", help="set debug to 1 for debug information", type=int)
    args = parser.parse_args()

    # Copy value(s) for the provided arguments
    if args.reserved:
        Reserved = args.reserved
    if args.filterenable:
        FilterEnable = args.filterenable
    if args.debug:
        Debug = args.debug

#    print "Reserved, FilterEnable = ", Reserved, FilterEnable
    FilterControlConfigure(Reserved, FilterEnable)
    
    