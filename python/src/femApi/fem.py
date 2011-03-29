'''
Created on 22 Mar 2011

@author: tcn
'''

# Identifier that indicates all chips
FEM_CHIP_ALL = 0

FEM_RTN_OK          = 0
FEM_RTN_UNKNOWNOPID = 1
FEM_RTN_ILLEGALCHIP = 2
FEM_RTN_BADSIZE     = 3

FEM_OP_ACQUIRE         = 1
FEM_OP_STOPACQUISITION = 2
FEM_OP_LOADPIXELCONFIG = 3

class Fem():
    '''
    Front-end Module implementation
    '''


    def __init__(self):
        '''
        Constructor
        '''
        pass
    
    def femCmd(self, chipId=None, id=None):
        
        if chipId == None:
            return FEM_RTN_ILLEGALCHIP
        
        if id == None:
            return FEM_RTN_UNKNOWNOPID
        
        return FEM_RTN_OK
    
if __name__ == "__main__":
    
    testFem = Fem();
    
    print 'femTest with no args returns: ', testFem.femCmd()
    print 'femTest with legal chip ID and cmd returns: ', testFem.femCmd(FEM_CHIP_ALL, FEM_OP_ACQUIRE)
    