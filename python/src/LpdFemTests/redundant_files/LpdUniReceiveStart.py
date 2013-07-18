'''
Created on Jun 12, 2013

    Modeled upon [carefully selected bit of] LpdFemGui

@author: ckd27546
'''

from LpdUniReceive import *
from LpdUniPlotData import *

import argparse
from PyQt4 import QtGui

class LpdUniReceiveStart():
    
    def __init__(self, app, femHost, femPort, asicModuleType, numFrames, fileName, debugLevel, viewDivisor, viewOffset):

        #Serves no further function but app (QApplication) must exist before instantiating liveViewWindow
        self.app = app

        self.cachedParams = { 'dataFilePath'      : '/tmp',
                              'fileWriteEnable'   : True,
                              'liveViewDivisor'   : 1,
                              'liveViewOffset'    : 0,
                              'asicModuleType'    : 0,
                              'debugLevel'        : 2,
                         }
        
        # Initialise variables from class arguments if provided
        self.dataListenAddr = femHost
        self.dataListenPort = femPort
        self.numFrames = numFrames
        self.cachedParams['asicModuleType'] = asicModuleType    # 0=supermodule, 1=single ASIC, 2=2-tile module, 3=stand-alone, 4=raw data, supermodule
        self.cachedParams['debugLevel'] = debugLevel
        self.cachedParams['liveViewDivisor'] = viewDivisor
        self.cachedParams['liveViewOffset'] = viewOffset
        
        if fileName == None:
            # Do not write to file if no path specified
            self.cachedParams['fileWriteEnable'] = False
        else:
            self.cachedParams['dataFilePath'] = fileName

        # Abort run flag used to signal to data receiver; #TODO: Redundant? Used by LpdUniReceive but never changed anywhere..
        self.abortRun = False
        
        # Create the live view window
        self.liveViewWindow = LpdUniPlotData(asicModuleType=self.cachedParams['asicModuleType'])
        self.liveViewWindow.show()
        
        
class DataReceiverThread(QtCore.QThread):
    
    def __init__(self, parent):
        QtCore.QThread.__init__(self)
        self.parentObject = parent

    def run(self):
        
        while not self.parentObject.abortRun:
            try:
                dataReceiver = LpdFemDataReceiver(self.parentObject.liveViewWindow.liveViewUpdateSignal, 
                                                  self.parentObject.dataListenAddr, self.parentObject.dataListenPort, self.parentObject.numFrames, self.parentObject.cachedParams, self.parentObject)
            except Exception as e:
                print "DataReceiverThread ERROR: failed to create data receiver: %s" % e
                sys.exit()
                return

            #TODO: required for thread to shutdown once the number of frames received?
            self.abortRun = True
            
            # Wait for the data receiver threads to complete
            try:
                dataReceiver.awaitCompletion()
            except Exception as e:
                print "DataReceiverThread ERROR: failed to await completion of data receiver threads: %s" % e
                return
        
def main(femHost, femPort, asicModuletype, numFrames, fileName, debugLevel, viewDivisor, viewOffset):
    
    app = QtGui.QApplication(sys.argv)
    obj = LpdUniReceiveStart(app, femHost, femPort, asicModuletype, numFrames, fileName, debugLevel, viewDivisor, viewOffset)

    drThread = DataReceiverThread(obj)
    drThread.start()

    sys.exit(app.exec_())

if __name__ == '__main__':

    # Default parser values
    asicModule  = 0
    femHost     = '10.0.0.1'
    femPort     = 61649
    numFrames   = 5
    fileName    = None
    debugLevel  = 0
    viewDivisor = 4
    viewOffset  = 3

    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="Note that writing to file only possible where hdf5 library installed locally", epilog="Example usage: 'python LpdUniReceiveStart.py --asicmodule 0 --femhost 127.0.0.1 --femport 50001 --file /tmp/superModData.hdf5 --numframes 10 --viewdivisor 4 --viewoffset 3'    [local host/port, superModule, 10 frames per readout, View 3rd image of every train]")

    parser.add_argument("--femhost",    help="switch LV on (1) or off (0)", type=str, default=femHost )
    parser.add_argument("--femport",    help="switch HV on (1) or off (0)", type=int, default=femPort )
    parser.add_argument("--asicmodule", help="Set ASIC Module (0=supermodule, 1=Asic, 2=2-Tile , 3=fem, 4=Raw data)", type=int, choices=[0, 1, 2, 3, 4], default=asicModule)
    parser.add_argument("--numframes",  help="Set number of frames", type=int, default=numFrames)
    parser.add_argument("--file",       help="absolute path including filename", type=str, default=fileName)
    parser.add_argument("--debuglevel", help="set debug level", type=int, choices=[0, 1, 2], default=debugLevel)
    parser.add_argument("--viewdivisor",help="display every n image (across train(s))", type=int, default=viewDivisor)
    parser.add_argument("--viewoffset", help="display image offset, e.g 0=first image, 1=2nd img, etc", type=int, default=viewOffset)
    args = parser.parse_args()

    if args.asicmodule != None:
        asicModule =  args.asicmodule
    
    if args.femhost != None:
        femHost = args.femhost
    
    if args.femport != None:
        femPort = args.femport
        
    if args.numframes != None:
        numFrames = args.numframes

    if args.file != None:
        fileName = args.file
    
    if args.debuglevel != None:
        debugLevel = args.debuglevel

    if args.viewdivisor != None:
        if args.viewdivisor == 0:
            print "Illegal value: viewdivisor must be greater than zero"
            sys.exit()
        else:
            viewDivisor = args.viewdivisor
        
    if args.viewoffset != None:
        viewOffset = args.viewoffset
    
    main(femHost, femPort, asicModule, numFrames, fileName, debugLevel, viewDivisor, viewOffset)
    

    