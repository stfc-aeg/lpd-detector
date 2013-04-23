import os, sys, time
from LpdFemGuiMainWindow import *
from LpdFemGuiLiveViewWindow import *
from LpdPowerCardManager import *
from LpdFemDataReceiver import *
from LpdDevice.LpdDevice import *
from FemClient.FemClient import *
from FemApi.FemConfig import *
from LpdReadoutConfig import *
from persistentDict import *

class PrintRedirector():
    
    def __init__(self, printFn):
        self.printFn = printFn
        
    def write(self, text):
        if ord(text[0]) != 10:
            self.printFn(text)
        
class LpdFemGui:
    
    DeviceDisconnected = 0
    DeviceIdle         = 1
    DeviceConfiguring  = 2
    DeviceReady        = 3
    DeviceRunning      = 4
    
    def __init__(self, app):

        self.app = app
        
        # Load default parameters from persistent file store
        self.defaultConfigPath = os.getcwd() + '/config'
        
        self.initialiseCachedParams()
        
        # Initialise device and default state
        self.device = LpdDevice()
        self.deviceState = LpdFemGui.DeviceDisconnected
        self.deviceErrString = ""
        self.femConfig = None
        
        self.dataListenAddr = '0.0.0.0'
        self.dataListenPort = 0
        self.numFrames      = 0
        
        self.loadedConfig   = {}
        
        # Create a power card manager instance
        self.pwrCard = LpdPowerCardManager(self, self.device)

        # Create the main window GUI and show it
        self.mainWindow= LpdFemGuiMainWindow(self)
        self.mainWindow.show()

        # Create the live view window but don't show it
        self.liveViewWindow = LpdFemGuiLiveViewWindow()
            
        # Redirect stdout to PrintRedirector
        sys.stdout = PrintRedirector(self.msgPrint)
        
    
    def initialiseCachedParams(self):
        '''
        Initialises default parameters from JSON file-backed store, or creates them
        if not existing in file from coded defaults
        '''   
        self.paramCacheFile = self.defaultConfigPath + "/lpdFemGui_config.json"
        
        self.cachedParams = PersistentDict(self.paramCacheFile, 'c', format='json')
        
        defaultParams = { 'connectionTimeout' : 5.0,
                          'femAddr'           : '192.168.2.2',
                          'femPort'           : 6969,
                          'readoutParamFile'  : self.defaultConfigPath + '/superModuleReadout.xml',
                          'fastParamFile'     : self.defaultConfigPath + '/ManualReset_longExposure_AsicControl.xml',
                          'slowParamFile'     : self.defaultConfigPath + '/AsicSlowParameters.xml',
                          'dataFilePath'      : '/tmp',
                          'hvBiasVolts'       : 50.0,
                          'numTrains'         : 8,
                          'externalTrigger'   : True,
                          'triggerDelay'      : 0,
                          'pixelGain'         : 0,
                          'pwrAutoUpdate'     : False,
                          'pwrUpdateInterval' : 0,
                          'runNumber'         : 0,
                          'fileWriteEnable'   : True,
                          'liveViewEnable'    : False,
                          'liveViewDivisor'   : 1,
                          'liveViewOffset'    : 0
                         }

        for param in defaultParams:
            if not self.cachedParams.has_key(param):
                self.cachedParams[param] = defaultParams[param]
        
        self.cachedParams.sync()
        
    def getCachedParam(self, param):
        
        if self.cachedParams.has_key(param):
            return self.cachedParams[param]
        else:
            return None
    
    def setCachedParam(self, param, val):
        
        if not self.cachedParams.has_key(param) or self.cachedParams[param] != val:
            self.cachedParams[param] = val
            self.cachedParams.sync()
            if self.deviceState == LpdFemGui.DeviceReady:
                self.deviceState = LpdFemGui.DeviceIdle
            
    def deviceConnect(self, addressStr, portStr):
        
        rc = self.device.open(addressStr, int(portStr), timeout=self.cachedParams['connectionTimeout'])
        if rc != LpdDevice.ERROR_OK:
            self.deviceState = LpdFemGui.DeviceDisconnected
            self.deviceErrString = "ERROR: connection failed: %s" % self.device.errorStringGet()
        else:
            self.deviceState = LpdFemGui.DeviceIdle
            self.deviceErrString = ""
        
    def deviceDisconnect(self):
        
        self.device.close()
        self.deviceState = LpdFemGui.DeviceDisconnected

    def cleanup(self):
        
        self.cachedParams.sync()
        
    def femConfigGet(self):
    
        if self.deviceState != LpdFemGui.DeviceDisconnected:
            self.femConfig = self.device.femClient.configRead()
                   
    def femConfigUpdate(self, net_mac, net_ip, net_mask, 
                        net_gw, temp_high, temp_crit, 
                        sw_major, sw_minor, fw_major, fw_minor,
                        hw_major, hw_minor, board_id, board_type):
        
        theConfig = FemConfig(net_mac, net_ip, net_mask, 
                        net_gw, temp_high, temp_crit, 
                        sw_major, sw_minor, fw_major, fw_minor,
                        hw_major, hw_minor, board_id, board_type)

        if self.deviceState != LpdFemGui.DeviceDisconnected:        
            self.device.femClient.configWrite(theConfig)
        
    def deviceConfigure(self):

        self.deviceState = LpdFemGui.DeviceConfiguring
        self.runStateUpdate()
                
        # Clear current loaded configuration 
        self.loadedConfig= {}        
        self.msgPrint("Loading readout parameters from file %s" % self.cachedParams['readoutParamFile'])
        try:
            readoutConfig = LpdReadoutConfig(self.cachedParams['readoutParamFile'], fromFile=True)
        except LpdReadoutConfigError as e:
            self.msgPrint("Error loading readout parameters: %s" % e)
            self.deviceState = LpdFemGui.DeviceIdle
            return

        for (param, value) in readoutConfig.parameters():
            rc = self.device.paramSet(param, value)
            if rc != LpdDevice.ERROR_OK:
                self.msgPrint('Setting parameter %s failed (rc=%d) : %s' % (param, rc, self.device.errorStringGet()))
                self.deviceState = LpdFemGui.DeviceIdle
                return
            try:
                self.loadedConfig[param] = value
            except Exception as e:
                print >> sys.stderr, "%s", e

        self.msgPrint("Loading ASIC slow parameters from file %s" % self.cachedParams['slowParamFile'])
        rc = self.device.paramSet('femAsicSlowControlParams', self.cachedParams['slowParamFile'])
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting ASIC slow parameter file to %s failed (rc=%d) : %s" % 
                          (self.cachedParams['slowParamFile'], rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return
            
        self.msgPrint("Loading ASIC fast command sequence from file %s" % self.cachedParams['fastParamFile'])
        rc = self.device.paramSet('femAsicFastCmdSequence', self.cachedParams['fastParamFile'])
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting ASIC fast command sequence file to %s failed (rc=%d) : %s" % 
                          (self.cachedParams['fastParamFile'], rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return
            
        self.msgPrint("Uploading configuration to LPD FEM device...")
        rc = self.device.configure()
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Configuration upload failed (rc=%d) : %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return
        
        # Store values of data receiver address, port and number of frames
        try:
            self.dataListenAddr = self.loadedConfig['tenGig0DestIp']
            self.dataListenPort = self.loadedConfig['tenGig0DestPort']
            self.numFrames      = self.loadedConfig['femNumTestCycles']
        except Exception as e:
            print >> sys.stderr, "Got exception storing reaodut config variables", e 
                
        self.deviceState = LpdFemGui.DeviceReady
    
    def deviceRun(self):
            
        # Increment the run number
        self.cachedParams['runNumber'] = self.cachedParams['runNumber'] + 1
        
        # Create and LpdFemDataReceiver instance to launch readout threads
        try:
            dataReceiver = LpdFemDataReceiver(self.liveViewWindow.liveViewUpdateSignal, self.mainWindow.runStatusSignal,
                                          self.dataListenAddr, self.dataListenPort, self.numFrames, self.cachedParams)
        except Exception as e:
            print >> sys.stderr, "Exception creating data receiver", e
            
        self.deviceState = LpdFemGui.DeviceRunning
        self.runStateUpdate()        

        rc = self.device.start()
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Acquisition start failed (rc=%d) : %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            
        dataReceiver.awaitCompletion()
        self.deviceState = LpdFemGui.DeviceReady
        
    def msgPrint(self, message):
        self.mainWindow.messageSignal.emit(message)
        
    def runStateUpdate(self):
        self.mainWindow.runStateSignal.emit()
         
def main():
        
    app = QtGui.QApplication(sys.argv)  
    lpdFemGui = LpdFemGui(app)
    
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()
    