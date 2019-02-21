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
    
    def __init__(self, app, femHost, femPort, asicModuleType, num_frames, fileName, debugLevel, viewDivisor, viewOffset):

        #Serves no further function but app (QApplication) must exist before instantiating live_view_window
        self.app = app

        self.cached_params = { 'dataFilePath'      : '/tmp',
                              'fileWriteEnable'   : True,
                              'liveViewDivisor'   : 1,
                              'liveViewOffset'    : 0,
                              'asicModuleType'    : 0,
                              'debugLevel'        : 2,
                         }
        
        # Initialise variables from class arguments if provided
        self.data_listen_addr = femHost
        self.data_listen_port = femPort
        self.num_frames = num_frames
        self.cached_params['asicModuleType'] = asicModuleType    # 0=supermodule, 1=single ASIC, 2=2-tile module, 3=stand-alone, 4=raw data, supermodule
        self.cached_params['debugLevel'] = debugLevel
        self.cached_params['liveViewDivisor'] = viewDivisor
        self.cached_params['liveViewOffset'] = viewOffset
        
        if fileName == None:
            # Do not write to file if no path specified
            self.cached_params['fileWriteEnable'] = False
        else:
            self.cached_params['dataFilePath'] = fileName

        # Abort run flag used to signal to data receiver; #TODO: Redundant? Used by LpdUniReceive but never changed anywhere..
        self.abort_run = False
        
        # Create the live view window
        self.live_view_window = LpdUniPlotData(asicModuleType=self.cached_params['asicModuleType'])
        self.live_view_window.show()
        
        
class DataReceiverThread(QtCore.QThread):
    
    def __init__(self, parent):
        QtCore.QThread.__init__(self)
        self.parentObject = parent

    def run(self):
        
        while not self.parentObject.abort_run:
            try:
                dataReceiver = LpdFemDataReceiver(self.parentObject.live_view_window.liveViewUpdateSignal, 
                                                  self.parentObject.data_listen_addr, self.parentObject.data_listen_port, self.parentObject.num_frames, self.parentObject.cached_params, self.parentObject)
            except Exception as e:
                print "DataReceiverThread ERROR: failed to create data receiver: %s" % e
                sys.exit()
                return

            #TODO: required for thread to shutdown once the number of frames received?
            self.abort_run = True
            
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
    

    