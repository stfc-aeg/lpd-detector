'''
    Author: ckd27546
    
    Created: 14 November 2012
'''

class DigitalControlConfigure():

    def __init__(self, Reserved=0, Reset3= 0, Reset2=0, Reset1=0, ClockCounterOffset=0, ClockSelect=0):
        '''
            DigitalControlConfigure allows the user to specify up to all six of the different parts of the Digital Control Slow Control Section
        '''
        
        """ REVERSE BIT ORDER? """
        
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
        #bitPosition += 7

        # Reserved occupies the first four bits (0-3)
        Reserved = Reserved << bitPosition


        # Bit shift each part in to their relative position within the Digital Control section


        total = Reserved + Reset3 + Reset2 + Reset1 + ClockCounterOffset + ClockSelect

        print "total = ", total

if __name__ == "__main__":

        
    DigitalControlConfigure(Reserved=0, Reset3= 0, Reset2=36, Reset1=56, ClockCounterOffset=56, ClockSelect=32)