'''
Created on Jun 18, 2013

@author: tcn45
'''

from __future__ import print_function

import argparse
import numpy as np
import socket
import time

class LpdFemUdpProducerError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)

class LpdFemUdpProducer(object):
 
    ModuleTypeSuperModule = 0
    ModuleTypeTwoTile     = 1
    
    PatternTypePerAsic    = 0
    PatternTypePerPixel   = 1
    
    def __init__(self, host, port, frames, images, module, pattern, interval, display, quiet):
        
        self.host = host
        self.port = port
        self.frames = frames
        self.images = images
        self.module = module
        self.pattern = pattern
        self.interval = interval
        self.display = display
        self.quiet = quiet
        
        # Initialise shape of data arrays in terms of ASICs and pixels
        self.numAsicRows = 8
        self.numAsicCols = 16
        self.numPixelRowsPerAsic = 32
        self.numPixelColsPerAsic = 16
        self.numPixelRows = self.numAsicRows * self.numPixelRowsPerAsic
        self.numPixelCols = self.numAsicCols * self.numPixelColsPerAsic
        self.numPixels    = self.numPixelRows * self.numPixelCols
        self.numAsics     = self.numAsicRows * self.numAsicCols

        # Initialise an array representing a single image in the system
        self.image_array = np.empty((self.numPixelRows, self.numPixelCols), dtype=np.uint16)
                
        if self.module == LpdFemUdpProducer.ModuleTypeSuperModule:
            
            # Fill in image array with the appropriate values depending on the pattern type
            if self.pattern == LpdFemUdpProducer.PatternTypePerAsic:
                
                # Create pattern with constant value per ASIC, offset is to use full 12-bit range
                # over all ASICs
                asicVal = 0
                asicValOffset = 32
                for aRow in range(self.numAsicRows):
                    for aCol in range(self.numAsicCols):
                        pixelRowStart = aRow * self.numPixelRowsPerAsic
                        pixelRowEnd   = pixelRowStart + self.numPixelRowsPerAsic
                        pixelColStart = aCol * self.numPixelColsPerAsic
                        pixelColEnd   = pixelColStart + self.numPixelColsPerAsic
                        self.image_array[pixelRowStart:pixelRowEnd, pixelColStart:pixelColEnd] = asicVal
                        asicVal += asicValOffset
            elif self.pattern == LpdFemUdpProducer.PatternTypePerPixel:
                
                # Create pattern with constant value per pixel, offset is to use full 12-bit range
                # over all pixels
                pixelVal = 0
                pixelValOffset = 8
                for pRow in range(self.numPixelRowsPerAsic):
                    for pCol in range(self.numPixelColsPerAsic):
                        self.image_array[pRow::self.numPixelRowsPerAsic, pCol::self.numPixelColsPerAsic] = pixelVal
                        pixelVal += pixelValOffset
            
            else:
                raise LpdFemUdpProducerError("Illegal pattern type %d specified" % self.pattern)
            
            # Transpose rows of image array to get correct vertical orientation
            self.image_array[:,:] = self.image_array[::-1,:]
            
        elif self.module == LpdFemUdpProducer.ModuleTypeTwoTile:

            # For two-tile system, zero out array for unused tiles
            self.image_array[:] = 0

            if self.pattern == LpdFemUdpProducer.PatternTypePerAsic:

                # Create pattern with constant value per ASIC, offset is to use full 12-bit range
                # over all ASICs
                asicVal = 0
                asicValOffset = 256
                for aRow in range(1,2) + range(6,7):
                    for aCol in range(15,7,-1):
                        pixelRowStart = aRow * self.numPixelRowsPerAsic
                        pixelRowEnd   = pixelRowStart + self.numPixelRowsPerAsic
                        pixelColStart = aCol * self.numPixelColsPerAsic
                        pixelColEnd   = pixelColStart + self.numPixelColsPerAsic
                        self.image_array[pixelRowStart:pixelRowEnd, pixelColStart:pixelColEnd] = asicVal
                        asicVal += asicValOffset
                        
            elif self.pattern == LpdFemUdpProducer.PatternTypePerPixel:

                # Create pattern with constant value per pixel, offset is to use full 12-bit range
                # over all pixels
                pixelVal = 0
                pixelValOffset = 8
                for pRow in range(self.numPixelRowsPerAsic):
                    for pCol in range(self.numPixelColsPerAsic):
                        pixelColStart = pCol+(self.numPixelColsPerAsic*8)
                        pixelColEnd   = pCol+(self.numPixelColsPerAsic*16)
                        self.image_array[pRow+32, pixelColStart:pixelColEnd:self.numPixelColsPerAsic] = pixelVal
                        self.image_array[pRow+192, pixelColStart:pixelColEnd:self.numPixelColsPerAsic] = pixelVal
                        pixelVal += pixelValOffset
            
            else:
                raise LpdFemUdpProducerError("Illegal pattern type %d specified" % self.pattern)
                
        else:
            raise LpdFemUdpProducerError("Illegal module type %d specified" % self.module)
    
        # Transform the image array to LPD data stream order
        pixelStream = np.empty(self.numPixels * self.images, dtype=np.uint16)
        streamOffset = 0
        for row in range(self.numPixelRowsPerAsic):
            for col in range(self.numPixelColsPerAsic):
                pixelStream[streamOffset:(streamOffset + self.numAsics)] = \
                    self.image_array[row::self.numPixelRowsPerAsic, col::self.numPixelColsPerAsic].reshape(self.numAsics)
                streamOffset += self.numAsics
        
        # Copy transformed data stream to repeat for number of images per train
        for image in range(1,self.images):
            streamOffset = image * self.numPixels
            pixelStream[streamOffset:(streamOffset+self.numPixels)] = pixelStream[0:self.numPixels] 

        # Convert data stream to byte stream for transmission
        self.byteStream = pixelStream.tostring()

        # Initialise monitoring variables
        self.framesSent = 0
        self.packetsSent = 0
        self.totalBytesSent = 0
        
        # Initialise the run state
        self.running = False
        
    def run(self):
        
        self.payloadLen = 8000
        startOfFrame    = 0x80000000
        endOfFrame      = 0x40000000

        print("Starting LPD data transmission to address", self.host, "port", self.port, "..." )
        
        self.running = True
                
        # Open UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Create packet trailer
        trailer = np.zeros(2, dtype=np.uint32)
       
        self.framesSent = 0
        self.packetsSent = 0
        self.totalBytesSent = 0
        
        runStartTime = time.time()
        
        for frame in range(self.frames):
            
            bytesRemaining = len(self.byteStream) 
            
            streamPosn = 0
            packetCounter = 0
            bytesSent = 0
            
            frameStartTime = time.time()
            
            while bytesRemaining > 0:
            
                # Calculate packet size and construct trailer
                trailer[0] = frame
                if bytesRemaining <= self.payloadLen:
                    bytesToSend = bytesRemaining
                    trailer[1] = packetCounter | endOfFrame
                else:
                    bytesToSend = self.payloadLen
                    trailer[1] = packetCounter | startOfFrame if packetCounter == 0 else packetCounter

                # Append trailer to current packet
                packet = self.byteStream[streamPosn:streamPosn+bytesToSend] + trailer.tostring()
                
                # Transmit packet
                bytesSent += sock.sendto(packet, (self.host, self.port))
                            
                bytesRemaining -= bytesToSend
                packetCounter += 1
                streamPosn += bytesToSend
                 
            if not self.quiet:
                print("  Sent frame", frame, "packets", packetCounter, "bytes", bytesSent)
                 
            self.framesSent     += 1
            self.packetsSent    += packetCounter
            self.totalBytesSent += bytesSent

            # Break out of loop if external stop received
            if self.running == False:
                break
            
            # Calculate wait time and sleep so that frames are sent at requested intervals            
            frameEndTime = time.time()
            waitTime = (frameStartTime + self.interval) - frameEndTime
            if waitTime > 0:
                time.sleep(waitTime)
       
        runTime = time.time() - runStartTime
             
        # Close socket
        sock.close()
        
        print("%d frames completed, %d bytes sent in %.3f secs" % (self.framesSent, self.totalBytesSent, runTime))
        
        if self.display:
            self.displayImage()
    
    def stop(self):
        
        self.running = False
                
    def displayImage(self):

        import matplotlib.pyplot as plt
 
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        img = ax.imshow(self.image_array)
        plt.show()       
        
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="LpdFemUdpProducer - generate a simulated LPD FEM UDP data stream")
    
    parser.add_argument('--host', type=str, default='127.0.0.1', 
                        help="select destination host IP address")
    parser.add_argument('--port', type=int, default=61649,
                        help='select destination host IP port')
    parser.add_argument('--frames', '-n', type=int, default=1,
                        help='select number of frames to transmit')
    parser.add_argument('--images', '-i', type=int, default=1,
                        help='select number of images per frame to transmit')
    parser.add_argument('--module', '-m', type=int, default=0, choices=[0, 1],
                        help='select module type (0=supermodule, 1=two-tile)')
    parser.add_argument('--pattern', '-p', type=int, default=0, choices=[0, 1],
                        help='select image pattern (0=per ASIC, 1=per pixel)')
    parser.add_argument('--interval', '-t', type=float, default=0.1,
                        help="select frame interval in seconds")
    parser.add_argument('--display', "-d", action='store_true',
                        help="Enable diagnostic display of generated image")
    parser.add_argument('--quiet', "-q", action="store_true",
                        help="Suppress detailed print during operation")
    
    args = parser.parse_args()

    producer = LpdFemUdpProducer(**vars(args))
    producer.run()
    