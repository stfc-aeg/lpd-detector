'''
Created on Apr 23, 2013

@author: tcn45
'''

class LpdFrameContainer(object):
    '''
        LpdFrameContainer - data container class to contain UDP payload and metadata
        (such as timestamp, packet, etc)
    '''
    def __init__(self, frameNumber):
        self.rawImageData = ""
        self.frameNumber = frameNumber
        self.timeStampSof = 0.0
        self.timeStampEof = 0.0


class LpdImageContainer(object): 
                        
    def __init__(self, runNumber, frameNumber, imageNumber):
        self.imageArray = None
        self.runNumber = runNumber
        self.frameNumber = frameNumber
        self.imageNumber = imageNumber
    
class LpdRunStatusContainer(object):
    
    def __init__(self, framesReceived, framesProcessed, imagesProcessed, dataBytesReceived):
        
        self.framesReceived  = framesReceived
        self.framesProcessed = framesProcessed
        self.imagesProcessed = imagesProcessed
        self.dataBytesReceived = dataBytesReceived
    