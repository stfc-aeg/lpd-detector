from LpdDataDisplayMainWindow import *
from LpdFemGuiLiveViewWindow import *
from LpdFemDataReceiver import *
from persistentDict import *
import os

class LpdDataDisplay:
    
    def __init__(self, app):

        self.app = app
        
        # Pick up path to config file from environment, otherwise default to config directory
        # in current working directory
        self.defaultConfigPath = os.getenv('LPD_FEM_GUI_CONFIG_PATH', os.getcwd() + '/ConfigFiles')
        
        # Load default parameters from persistent file store (or create them if file doesn't exist)
        self.paramCacheFile = self.defaultConfigPath + "/lpdDataDisplay_config.json"
        
        self.cachedParams = PersistentDict(self.paramCacheFile, 'c', format='json')
        
        defaultParams = { 'readoutParamFile'  : self.defaultConfigPath + '/dummy.xml',
                          'fastParamFile'     : self.defaultConfigPath + '/dummy.xml',
                          'slowParamFile'     : self.defaultConfigPath + '/dummy.xml',
                          'dataFilePath'      : '/tmp',
                          'numTrains'         : 4,
                          'runNumber'         : 0,
                          'fileWriteEnable'   : True,
                          'liveViewEnable'    : False,
                          'liveViewDivisor'   : 1,
                          'liveViewOffset'    : 0,
                          'asicModuleType'    : 0,  #0=super module, 2=2-tile module
                         }
        #TODO: Sort this hack out
        self.Params = defaultParams
        
        # Load default parameters into cache if not already existing        
        for param in defaultParams:
            if not self.cachedParams.has_key(param):
                self.cachedParams[param] = defaultParams[param]
        
        # Sync cached parameters back to file
        self.cachedParams.sync()        
        
        self.dataListenAddr = '10.0.0.1'
        self.dataListenPort = 61649
        self.numFrames      = 2

        # Create the main window GUI and show it
        self.mainWindow= LpdDataDisplayMainWindow(self)

        # Create the live view window but don't show it
        self.liveViewWindow = LpdFemGuiLiveViewWindow()
            
        # Abort run flag used to signal to data receiver
        self.abortRun = False
   
    def deviceRun(self):
            
        # Increment the run number
        self.cachedParams['runNumber'] = self.cachedParams['runNumber'] + 1
        
        # Clear abort run flag
        self.abortRun = False

        # Create and LpdFemDataReceiver instance to launch readout threads
        try:
            dataReceiver = LpdFemDataReceiver(self.liveViewWindow.liveViewUpdateSignal, self.mainWindow.runStatusSignal,
                                              self.dataListenAddr, self.dataListenPort, self.numFrames, self.cachedParams, self) 
#                                              self.dataListenAddr, self.dataListenPort, self.numFrames, self.Params, self)
#                                              self.dataListenAddr, self.dataListenPort, self.numFrames, {}, self)
            
        except Exception as e:
            print "ERROR: failed to create data receiver: %s" % e
            return

        # Wait for the data receiver threads to complete
        try:
            dataReceiver.awaitCompletion()
        except Exception as e:
            print "ERROR: failed to await completion of data receiver threads: %s" % e
            
def main():
        
    app = QtGui.QApplication(sys.argv)  
    lpdFemGui = LpdDataDisplay(app)
    
    #TODO: Replace this  hack with proper implementation..
    lpdFemGui.mainWindow.deviceRun()
    
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()
    
