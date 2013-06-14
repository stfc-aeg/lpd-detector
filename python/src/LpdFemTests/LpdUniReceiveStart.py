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
    
    def __init__(self, app, femHost, femPort, asicModuleType, numFrames, fileName, debugLevel):

        #Serves no further function but app (QApplication) must exist before instantiating liveViewWindow
        self.app = app

        self.cachedParams = { 'dataFilePath'      : '/tmp',
                              'fileWriteEnable'   : True,
                              'liveViewDivisor'   : 1,
                              'liveViewOffset'    : 0,
                              'asicModuleType'    : 0,  #0=super module, 2=2-tile module, #TODO: Add stand-alone fem in future for jac
                              'debugLevel'        : 2,
                         }
        
        # Initialise variables from class arguments if provided
        self.dataListenAddr = femHost
        self.dataListenPort = femPort
        self.numFrames = numFrames
        self.cachedParams['asicModuleType'] = asicModuleType    # 0=supermodule, 1=single ASIC, 2=2-tile module, 3=stand-alone, 4=raw data, supermodule
        self.cachedParams['debugLevel'] = debugLevel
        
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
        
def main(femHost, femPort, asicModuletype, numFrames, fileName, debugLevel):
    
    app = QtGui.QApplication(sys.argv)
    obj = LpdUniReceiveStart(app, femHost, femPort, asicModuletype, numFrames, fileName, debugLevel)

    drThread = DataReceiverThread(obj)
    drThread.start()

    sys.exit(app.exec_())

if __name__ == '__main__':


    # Create parser object and arguments
    parser = argparse.ArgumentParser(description=" ", epilog="Example usage: 'python LpdUniReceiveStart.py --asicmodule 0 --file /tmp/superModData.hdf5 --numframes 10 --debuglevel 2'")

    parser.add_argument("--femhost",    help="switch LV on (1) or off (0)", type=str, default='10.0.0.1' )
    parser.add_argument("--femport",    help="switch HV on (1) or off (0)", type=int, default=61649 )
    parser.add_argument("--asicmodule", help="Set ASIC Module (0=supermodule, 1=Asic, 2=2-Tile , 3=fem, 4=Raw data)", type=int, choices=[0, 1, 2, 3, 4], default=0)
    parser.add_argument("--numframes",  help="Set number of frames", type=int, default=4)
    parser.add_argument("--file",       help="absolute path including filename", type=str, default=None)
    parser.add_argument("--debuglevel", help="set debug level", type=int, choices=[0, 1, 2], default=0)
    args = parser.parse_args()

    asicModule = 0
    if args.asicmodule != None:
        asicModule =  args.asicmodule
    
    femHost = '10.0.0.1'
    if args.femhost != None:
        femHost = args.femhost
    
    femPort = 61649
    if args.femport != None:
        femPort = args.femport
        
    numFrames = 0
    if args.numframes != None:
        numFrames = args.numframes

    fileName = None
    if args.file != None:
        fileName = args.file
    
    debugLevel = 0
    if args.file != None:
        debugLevel = args.debuglevel
    
#    print "asicModule = ", asicModule
#    print "femHost =    ",femHost
#    print "femPort =    ",femPort
#    print "numFrames =  ",numFrames
#    print "file(Path) = ", fileName
    
    main(femHost, femPort, asicModule, numFrames, fileName, debugLevel)
    

    