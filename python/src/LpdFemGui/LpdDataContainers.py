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
                        
    def __init__(self, run_number, frame_number, image_number):
        self.image_array = None
        self.run_number = run_number
        self.frame_number = frame_number
        self.image_number = image_number
    
class LpdRunStatusContainer(object):
    
    def __init__(self, frames_received, frames_processed, images_processed, data_bytes_received):
        
        self.frames_received  = frames_received
        self.frames_processed = frames_processed
        self.images_processed = images_processed
        self.data_bytes_received = data_bytes_received
    