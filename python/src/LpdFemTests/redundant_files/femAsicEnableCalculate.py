import sys

def bitShifting(arg1, direction):
    ''' Bit shift arg1 by direction bits (positive = left shifting, negative = right shifting) '''
    if direction > 0:
        newValue = arg1 << direction
    else:
        newValue = arg1 >> (direction* -1)
    return newValue

def femAsicEnableCalculate(userMask):
    '''  Convert user's femAsicEnableMask selection into fem's own format
        e.g.
            user format: [0] = ASIC1-ASIC32, [1] = 33-64, etc (where 0x1=ASIC1,  0x2=ASIC2, etc)
            fem format:  [0] = ASIC1-4, 17-20, 33-37, etc; [1] = ASIC5-8, 21-24, ..
    '''
    
    femMask = [0x0, 0x0, 0x0, 0x0]

    # Replace hardcoded code with for loops
    bitMask = 0x0000000F
    direction = 28
    maskIndex = 0
    
    for index in range(8):
        maskedValue     = userMask[0] & bitMask
        shifted         = bitShifting( maskedValue, direction)
        femMask[maskIndex] = (femMask[maskIndex] | shifted)
        # Update counters
        if index % 7 == 3:
            direction -= 8
        else:
            direction -= 4
        if maskIndex == 3:
            maskIndex = 0
        else:
            maskIndex += 1
        bitMask = bitMask << 4
        
    bitMask = 0x0000000F
    direction = 20
    maskIndex = 0
    
    for index in range(8):
        maskedValue     = userMask[1] & bitMask
        shifted         = bitShifting( maskedValue, direction)
        femMask[maskIndex] = (femMask[maskIndex] | shifted)
        # Update counters
        if index % 7 == 3:
            direction -= 8
        else:
            direction -= 4
        if maskIndex == 3:
            maskIndex = 0
        else:
            maskIndex += 1
        bitMask = bitMask << 4

    bitMask = 0x0000000F
    direction = 12
    maskIndex = 0
    
    for index in range(8):
        maskedValue     = userMask[2] & bitMask
        shifted         = bitShifting( maskedValue, direction)
        femMask[maskIndex] = (femMask[maskIndex] | shifted)
        # Update counters
        if index % 7 == 3:
            direction -= 8
        else:
            direction -= 4
        if maskIndex == 3:
            maskIndex = 0
        else:
            maskIndex += 1
        bitMask = bitMask << 4

    bitMask = 0x0000000F
    direction = 4
    maskIndex = 0
    
    for index in range(8):
        maskedValue     = userMask[3] & bitMask
        shifted         = bitShifting( maskedValue, direction)
        femMask[maskIndex] = (femMask[maskIndex] | shifted)
        # Update counters
        if index % 7 == 3:
            direction -= 8
        else:
            direction -= 4
        if maskIndex == 3:
            maskIndex = 0
        else:
            maskIndex += 1
        bitMask = bitMask << 4

#    femMask[0] = (femMask[0] | (userMask[0]     & 0x0000000F) << 28)
#    femMask[1] = (femMask[1] | ( (userMask[0]   & 0x000000F0) << 24) )
#    femMask[2] = (femMask[2] | ( (userMask[0]   & 0x00000F00) << 20) )
#    femMask[3] = (femMask[3] | ( (userMask[0]   & 0x0000F000) << 16) )
#    femMask[0] = (femMask[0] | ( (userMask[0]   & 0x000F0000) <<  8) )
#    femMask[1] = (femMask[1] | ( (userMask[0]   & 0x00F00000) <<  4) )
#    femMask[2] = (femMask[2] | ( (userMask[0]   & 0x0F000000)      ) )
#    femMask[3] = (femMask[3] | ( (userMask[0]   & 0xF0000000) >>  4) )
#
#    femMask[0] = (femMask[0] | ( (userMask[1]   & 0x0000000F) << 20) )
#    femMask[1] = (femMask[1] | ( (userMask[1]   & 0x000000F0) << 16) )
#    femMask[2] = (femMask[2] | ( (userMask[1]   & 0x00000F00) << 12) )
#    femMask[3] = (femMask[3] | ( (userMask[1]   & 0x0000F000) <<  8) )
#    femMask[0] = (femMask[0] | ( (userMask[1]   & 0x000F0000)      ) )
#    femMask[1] = (femMask[1] | ( (userMask[1]   & 0x00F00000) >>  4) )
#    femMask[2] = (femMask[2] | ( (userMask[1]   & 0x0F000000) >>  8) )
#    femMask[3] = (femMask[3] | ( (userMask[1]   & 0xF0000000) >> 12) )
#
#    femMask[0] = (femMask[0] | ( (userMask[2]   & 0x0000000F) << 12) )
#    femMask[1] = (femMask[1] | ( (userMask[2]   & 0x000000F0) <<  8) )
#    femMask[2] = (femMask[2] | ( (userMask[2]   & 0x00000F00) <<  4) )
#    femMask[3] = (femMask[3] | ( (userMask[2]   & 0x0000F000)      ) )
#    femMask[0] = (femMask[0] | ( (userMask[2]   & 0x000F0000) >>  8) )
#    femMask[1] = (femMask[1] | ( (userMask[2]   & 0x00F00000) >> 12) )
#    femMask[2] = (femMask[2] | ( (userMask[2]   & 0x0F000000) >> 16) )
#    femMask[3] = (femMask[3] | ( (userMask[2]   & 0xF0000000) >> 20) )
#
#    femMask[0] = (femMask[0] | ( (userMask[3]   & 0x0000000F) <<  4) )
#    femMask[1] = (femMask[1] | ( (userMask[3]   & 0x000000F0)      ) )
#    femMask[2] = (femMask[2] | ( (userMask[3]   & 0x00000F00) >>  4) )
#    femMask[3] = (femMask[3] | ( (userMask[3]   & 0x0000F000) >>  8) )
#    femMask[0] = (femMask[0] | ( (userMask[3]   & 0x000F0000) >> 16) )
#    femMask[1] = (femMask[1] | ( (userMask[3]   & 0x00F00000) >> 20) )
#    femMask[2] = (femMask[2] | ( (userMask[3]   & 0x0F000000) >> 24) )
#    femMask[3] = (femMask[3] | ( (userMask[3]   & 0xF0000000) >> 28) )

    print "userMask => femMask\n==================="
    for idx in range(4):
        print  "%8X    %8X" % (userMask[idx], femMask[idx])
    return femMask

if __name__ == '__main__':

#    print len(sys.argv)
    # Check command line for host and port info    
    if len(sys.argv) == 5:
        userMask = [int(sys.argv[1], 16), int(sys.argv[2], 16), int(sys.argv[3], 16), int(sys.argv[4], 16)]
    else:
        # Nothing provided from command line; Use defaults
#        userMask = [0xFF000000, 0x0, 0x0, 0x0000FF00]
        userMask = [0x12345608, 0x12340678, 0x12045678, 0x10345678]

#    userMask = [0xFFFFFFFF, 0xFFFFFFF7, 0xFFFFFFFF, 0xFFFFFFFF]
    femAsicEnableCalculate(userMask)
