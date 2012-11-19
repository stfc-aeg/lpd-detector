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
    
if __name__ == "__main__":

    # Example usage:
    '''
        python LpdFemTests/redundant_files/FilterControlConfigure.py --reserved 278528 --filterenable 0
    '''
    
    # Define class arguments
    Reserved    = 0 #278528
    FilterEnable = 0 #0
    
    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="FilterControlConfigure.py - Accepts up to 2 arguments to set the functions compromising the Filter Control keyword and generates the 20 bit word used by the <filter_control> XML tag. ",
                                     epilog="The perceived wisdom is that the following function values are the default settings:\nreserved = 278528\nfilterenable = 0,\t Note: the parser ignores any argument set to 0 and therefore the default values of all of the two arguments is 0 if not provided.")

    parser.add_argument("--reserved", help="set the Reserved function (19 bits)", type=int)
    parser.add_argument("--filterenable", help="set the Filter Enable function (1 bit)", type=int)
    args = parser.parse_args()

    # Copy value(s) for the provided arguments
    if args.reserved:
        Reserved = args.reserved
    if args.filterenable:
        FilterEnable = args.filterenable

#    print "Reserved, FilterEnable = ", Reserved, FilterEnable
    FilterControlConfigure(Reserved, FilterEnable)
    
    