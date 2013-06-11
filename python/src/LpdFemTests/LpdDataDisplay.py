from LpdDataDisplayMainWindow import *
from LpdFemGuiLiveViewWindow import *
from LpdFemDataReceiver import *
from LpdDevice.LpdDevice import *
from FemClient.FemClient import *
from FemApi.FemConfig import *
from persistentDict import *
import os

class PrintRedirector():
    
    def __init__(self, printFn):
        self.printFn = printFn
        
    def write(self, text):
        if ord(text[0]) != 10:
            self.printFn(text)
        
class LpdDataDisplay:
    
    DeviceDisconnected = 0
    DeviceIdle         = 1
    DeviceConfiguring  = 2
    DeviceReady        = 3
    DeviceRunning      = 4
    
    def __init__(self, app):

        self.app = app
        
        # Pick up path to config file from environment, otherwise default to config directory
        # in current working directory
        self.defaultConfigPath = os.getenv('LPD_FEM_GUI_CONFIG_PATH', os.getcwd() + '/config')
        
        # Load default parameters from persistent file store
        self.initialiseCachedParams()
        
        # Initialise device and default state
        self.deviceState = LpdDataDisplay.DeviceDisconnected
        
        self.dataListenAddr = '10.0.0.1'
        self.dataListenPort = 61649
        self.numFrames      = 2

        # Create the main window GUI and show it
        self.mainWindow= LpdDataDisplayMainWindow(self)
        self.mainWindow.show()
        self.mainWindow.ui.runBtn.setEnabled(True)
        self.mainWindow.ui.operateGroupBox.setEnabled(True)
        
        # Create the live view window but don't show it
        self.liveViewWindow = LpdFemGuiLiveViewWindow()
            
        # Redirect stdout to PrintRedirector
        sys.stdout = PrintRedirector(self.msgPrint)
        
        # Abort run flag used to signal to data receiver
        self.abortRun = False
            
    def initialiseCachedParams(self):
        '''
        Initialises default parameters from JSON file-backed store, or creates them
        if not existing in file from coded defaults
        '''   
        self.paramCacheFile = self.defaultConfigPath + "/lpdFemGui_config.json"
        
        self.cachedParams = PersistentDict(self.paramCacheFile, 'c', format='json')
        
        defaultParams = { 'readoutParamFile'  : self.defaultConfigPath + '/superModuleReadout.xml',
                          'fastParamFile'     : self.defaultConfigPath + '/ManualReset_longExposure_AsicControl.xml',
                          'slowParamFile'     : self.defaultConfigPath + '/AsicSlowParameters.xml',
                          'dataFilePath'      : '/tmp',
                          'numTrains'         : 8,
                          'runNumber'         : 0,
                          'fileWriteEnable'   : True,
                          'liveViewEnable'    : False,
                          'liveViewDivisor'   : 1,
                          'liveViewOffset'    : 0,
                          'asicModuleType'    : 0,  #0=super module, 2=2-tile module
                         }

        # Load default parameters into cache if not already existing        
        for param in defaultParams:
            if not self.cachedParams.has_key(param):
                self.cachedParams[param] = defaultParams[param]
        
        # Sync cached parameters back to file
        self.cachedParams.sync()
        
    def deviceDisconnect(self):
        
        self.deviceState = LpdDataDisplay.DeviceDisconnected

    def cleanup(self):
        
        self.cachedParams.sync()
   
    def deviceRun(self):
            
        # Increment the run number
        self.cachedParams['runNumber'] = self.cachedParams['runNumber'] + 1
        
        # Clear abort run flag
        self.abortRun = False

        # Create and LpdFemDataReceiver instance to launch readout threads
        try:
            dataReceiver = LpdFemDataReceiver(self.liveViewWindow.liveViewUpdateSignal, self.mainWindow.runStatusSignal, 
                                              self.dataListenAddr, self.dataListenPort, self.numFrames, self.cachedParams, self)
        except Exception as e:
            self.msgPrint("ERROR: failed to create data receiver: %s" % e)
#            self.deviceState = LpdDataDisplay.DeviceIdle
            return
        
        # Set device state as running and trigger update of run state in GUI    
        self.deviceState = LpdDataDisplay.DeviceRunning

        # Wait for the data receiver threads to complete
        try:
            dataReceiver.awaitCompletion()
        except Exception as e:
            self.msgPrint("ERROR: failed to await completion of data receiver threads: %s" % e)
            
        # Signal device state as ready
        self.deviceState = LpdDataDisplay.DeviceReady
        
    def msgPrint(self, message):
        '''
        Sends a message to the GUI thread for display
        '''
        self.mainWindow.messageSignal.emit(message)
        
    def runStateUpdate(self):
        '''
        Sends a run state update to the GUI thread for display
        ''' 
        self.mainWindow.runStateSignal.emit()
         
def main():
        
    app = QtGui.QApplication(sys.argv)  
    lpdFemGui = LpdDataDisplay(app)
    
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()
    
