# Check in setParaValue() for list/integer type 
import types

class SlowCtrlParams(object):
 
    numPixels = 3
#   paramsDict = {'dictKey'                     : [width, posn, value(s)}    
    paramsDict = {'mux_decoder'                 : [3, 0, [-1] * 512 ],
                  'mux_decoder_default'         : [3, -1, -1],
                  'feedback_select'             : [1, 1536, [-1] * 512],
                  'feedback_select_default'     : [1, -1, -1],
                  'self_test_decoder'           : [3, 1537, [-1] * 512 ],
                  'self_test_decoder_default'   : [3, -1, -1],
                  'self_test_enable'            : [1, 3584, -1],
                  'daq_bias'                    : [5, 3585, [-1] * 512],
                  'daq_bias_default'            : [5, -1, -1],
                  'spare_bits'                  : [5, 3280, [-1] * 4],  # Special Case
                  '100x_filter_control'         : [20, 3825, -1],       # Special Case
                  'adc_clock_delay'             : [20, 3845, -1],       # Special Case
                  'digital_control'             : [8, 3865, [-1] * 6],  # Special Case - variable lengths
                  }
     
    def __init__(self):
        
        self.pixelGain = range(SlowCtrlParams.numPixels)
        self.pixelGain2 = range(SlowCtrlParams.numPixels)

    def getParamValue(self, dictKey):
        """ Obtains the three variables associated with the dictionary key 'dictKey' 
            and returns them as three variables (the third are in some cases a list) """
        
        width = 0xdeadbeef
        posn = 0xDeadBeef
        val = 0xDeadBeef
        
        # Does dictKey exist in the dictionary?
        if dictKey in self.paramsDict:
            result = self.paramsDict[dictKey]
            
            width = result[0]
            posn = result[1]
            val = result[2]
        else:
            print "\"" + dictKey + "\" doesn't exist."
        
        return width, posn, val
 
    def setParamValue(self, dictKey, index, value):
        """ updates the dictionary key 'dictKey' with the new value in 'value', 
            overwriting whatever used to be at position 'index' """
            
        # Does dictKey exist in the dictionary?
        if dictKey in self.paramsDict:
            # Save the old values that we want to retain
            result = self.paramsDict[dictKey]
            # Is the third variable a list or an integer?
            if isinstance(result[2], types.ListType):
                # it's a list; Remove the old value
                result[2].pop(index)
                # Insert the new value
                result[2].insert(index, value)
                
            elif isinstance(result[2], types.IntType):
                result[2] = value
            else:
                print "SetParamValue() Error: result[2] is neither a list nor an integer!"
                                
            # Overwrite the old value
            self.paramsDict[dictKey] = result

        else:
            print "\"" + dictKey + "\" doesn't exist."


if __name__ == '__main__':
    
    theParams = SlowCtrlParams()
    
#    theParams.getParamValue("mux_decoder_default")
    width, posn, val = theParams.getParamValue("self_test_decoder_default")
    print width, posn, val
    
    print "Changing self_test_decoder_default.."
    
    theParams.setParamValue("self_test_decoder_default", 1, 56)
    
    print "the new value:"
    width, posn, val = theParams.getParamValue("self_test_decoder_default")
    print width, posn, val


#    paramName = "pixelGain2"
#    paramIdx  = 2
#    
#         
#    print getattr(theParams, 'pixelGain')
#        
#    
#    getattr(theParams, paramName)[paramIdx] = 321
#        
#    
#    print getattr(theParams, paramName)
#    print getattr(theParams, paramName)[2]
#        
#    
#    print theParams.__dict__
#        
#    setattr(theParams, 'new', [3,2,1])
#    print theParams.__dict__
