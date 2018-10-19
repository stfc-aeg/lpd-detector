'''
Created on Apr 23, 2013

@author: tcn45
'''

import sys

# Test if running python 3
is_python3 = sys.version_info > (3,)

class LpdFrameContainer(object):
    '''
        LpdFrameContainer - data container class to contain UDP payload and metadata
        (such as timestamp, packet, etc)
    '''
    def __init__(self, frameNumber):
        self.rawImageData = b'' if is_python3 else ''
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
        
        self.frames_received  = framesReceived
        self.frames_processed = framesProcessed
        self.images_processed = imagesProcessed
        self.data_bytes_received = dataBytesReceived
    