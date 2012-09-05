class SlowCtrlParams(object):
 
    numPixels = 3
#   paramsDict = {'dictKey' : [width, posn, [ 0, 1, ..]}    
    paramsDict = {'mux_decoder'     : [3, 0, [-1] * 512 ]
                  
                  }
     
    def __init__(self):
        
        self.pixelGain = range(SlowCtrlParams.numPixels)
        self.pixelGain2 = range(SlowCtrlParams.numPixels)

 
if __name__ == '__main__':
    
    theParams = SlowCtrlParams()
        
    paramName = "pixelGain2"
    paramIdx  = 2
    
         
    print getattr(theParams, 'pixelGain')
        
    
    getattr(theParams, paramName)[paramIdx] = 321
        
    
    print getattr(theParams, paramName)
    print getattr(theParams, paramName)[2]
        
    
    print theParams.__dict__
        
    setattr(theParams, 'new', [3,2,1])
    print theParams.__dict__
