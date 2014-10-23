from LpdFemGuiMainWindow import *
from LpdFemGuiLiveViewWindow import *
from LpdPowerCardManager import *
from LpdFemDataReceiver import *
from LpdEvrTimestampRecorder import *
from LpdDevice.LpdDevice import *
from FemClient.FemClient import *
from FemApi.FemConfig import *
from LpdReadoutConfig import *
from persistentDict import *
from ServoShutter import *
import os

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
        
        # Pick up path to config file from environment, otherwise default to config directory
        # in current working directory
        self.defaultConfigPath = os.getenv('LPD_FEM_GUI_CONFIG_PATH', os.getcwd() + '/config')
        
        # Load default parameters from persistent file store
        self.initialiseCachedParams()
        
        # Initialise device and default state
        self.device = LpdDevice()
        self.deviceState = LpdFemGui.DeviceDisconnected
        self.deviceErrString = ""
        self.femConfig = None
        
        self.dataListenAddr = '0.0.0.0'
        self.dataListenPort = 0
        self.numFrames      = 0
        
        self.lastDataFile = None
        
        self.loadedConfig   = {}
        
        # Create a power card manager instance
        self.pwrCard = LpdPowerCardManager(self, self.device)

        # Create the main window GUI and show it
        self.mainWindow= LpdFemGuiMainWindow(self)
        self.mainWindow.show()

        # Create an LPD ASIC tester instance
        self.asicTester = LpdAsicTester(self, self.device)

        # Create the live view window but don't show it
        self.liveViewWindow = LpdFemGuiLiveViewWindow(asicModuleType=self.cachedParams['asicModuleType'])

        try:
            self.asicWindow = LpdFemGuiAsicWindow(appMain=self)
            self.asicWindow.show()    # Hide window for now while testing

        except Exception as e:
            print >> sys.stderr, "LpdAsicTester initialisation exception: %s" % e
            
        # Redirect stdout to PrintRedirector
        sys.stdout = PrintRedirector(self.msgPrint)

        self.shutter = 0
        self.shutterEnabled = self.getCachedParam('arduinoShutterEnable')

        # Connect to shutter if arduinoShutterEnable set in .json file
        if self.shutterEnabled:        

            usbport = self.getCachedParam('arduinoShutterPort')
            try:
                self.shutter = ServoShutter(usbport)
                # Ensure shutter shut when GUI starts
                self.shutter.move(0)
            except Exception as e:
                self.msgPrint("Shutter %s" % e)

        # Abort run flag used to signal to data receiver
        self.abortRun = False
            
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
                          'cmdSequenceFile'   : self.defaultConfigPath + '/Command_LongExposure_V2.xml',
                          'setupParamFile'    : self.defaultConfigPath + '/Setup_LowPower.xml',
                          'dataFilePath'      : '/tmp',
                          'hvBiasVolts'       : 50.0,
                          'numTrains'         : 8,
                          'externalTrigger'   : True,
                          'triggerDelay'      : 0,
                          'pwrAutoUpdate'     : False,
                          'pwrUpdateInterval' : 0,
                          'runNumber'         : 0,
                          'fileWriteEnable'   : True,
                          'liveViewEnable'    : False,
                          'liveViewDivisor'   : 1,
                          'liveViewOffset'    : 0,
                          'evrMcastGroup'     : '239.255.16.17',
                          'evrMcastPort'      : 10151,
                          'evrMcastInterface' : '172.21.22.69',
                          'evrRecordEnable'   : True,
                          'femAsicGainOverride' : 8,
                          'femAsicPixelFeedbackOverride' : 0,
                          'asicModuleType'      : 0,
                         }

        # List of parameter names that don't need to force a system reconfigure
        self.nonVolatileParams = ('fileWriteEnable', 'liveViewEnable', 'liveViewDivisor', 'liveViewOffset',
                                  'pwrAutoUpdate', 'pwrUpdateInterval', 'dataFilePath', 'hvBiasBolts')

        # Load default parameters into cache if not already existing        
        for param in defaultParams:
            if not self.cachedParams.has_key(param):
                self.cachedParams[param] = defaultParams[param]
        
        # Sync cached parameters back to file
        self.cachedParams.sync()
        
    def getCachedParam(self, param):
        
        if self.cachedParams.has_key(param):
            return self.cachedParams[param]
        else:
            return None
    
    def setCachedParam(self, param, val):
        '''
        Update a cached parameter with a new value and flag that the device needs
        reconfiguring if the parameter is volatile
        '''
        if not self.cachedParams.has_key(param) or self.cachedParams[param] != val:
            self.cachedParams[param] = val
            self.cachedParams.sync()
            if not param in self.nonVolatileParams:
                if self.deviceState == LpdFemGui.DeviceReady:
                    self.deviceState = LpdFemGui.DeviceIdle
            
    def deviceConnect(self, addressStr, portStr):
        
        rc = self.device.open(addressStr, int(portStr), timeout=self.cachedParams['connectionTimeout'],
                              asicModuleType=self.cachedParams['asicModuleType'])
        if rc != LpdDevice.ERROR_OK:
            self.deviceState = LpdFemGui.DeviceDisconnected
            self.deviceErrString = "ERROR: connection failed: %s" % self.device.errorStringGet()
        else:
            self.deviceState = LpdFemGui.DeviceIdle
            self.deviceErrString = ""
            self.mainWindow.testTab.femConnectionSignal.emit(True)
        
    def deviceDisconnect(self):
        
        self.device.close()
        self.deviceState = LpdFemGui.DeviceDisconnected
        self.mainWindow.testTab.femConnectionSignal.emit(False)

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
        
    def deviceConfigure(self, currentParams=None):

        self.deviceState = LpdFemGui.DeviceConfiguring
        self.runStateUpdate()

        try:        
            # if currentParams not supplied, use self.cachedParams
            if not currentParams:
                currentParams  = self.cachedParams

        except Exception as e:
            print >> sys.stderr, "\ndeviceConfigure Exception: %s doesn't exist?" % e
        
#        parameters = ['readoutParamFile', 'femAsicGainOverride', 'testingReadoutParamFile', 'setupParamFile', 'testingSetupParamFile', 'cmdSequenceFile'
#                      'pixelGain', 'femAsicPixelFeedbackOverride', 'testingShortExposureFile', 'fileWriteEnable', 'liveViewEnable', 'arduinoShutterEnable']
#        print >> sys.stderr, "--------------------\nLpdFemGui settings:"
#        for key in currentParams.keys():
#            if key in parameters:
#                print >> sys.stderr, "  ", key, ":", currentParams[key]

        try:
            self.shutterEnabled = currentParams['arduinoShutterEnable']
            # Connect to shutter if shutter selected in GUI but not yet set up
            if self.shutterEnabled:       
    
                # Setup shutter unless already initialised?
                if self.shutter == 0:
    
                    usbport = self.getCachedParam('arduinoShutterPort')
                    try:
                        self.shutter = ServoShutter(usbport)
                        # Ensure shutter shut when GUI starts
                        self.shutter.move(0)
                    except Exception as e:
                        self.msgPrint("Shutter %s" % e)
            else:
                if self.shutter != 0:
                    # Close serial connection
                    self.shutter.__del__()
                    self.shutter = 0
        except Exception as e:
            print >> sys.stderr, "configurable issues: ", e

        # Clear current loaded configuration
        self.loadedConfig= {}
        
        # Load readout parameters from file       
        self.msgPrint("Loading Readout Params from file %s" % currentParams['readoutParamFile'])
        try:
            readoutConfig = LpdReadoutConfig(currentParams['readoutParamFile'], fromFile=True)
        except LpdReadoutConfigError as e:
            self.msgPrint("Error loading readout parameters: %s" % e)
            self.deviceState = LpdFemGui.DeviceIdle
            return

        # Set all parameters from file on device
        for (param, value) in readoutConfig.parameters():
            rc = self.device.paramSet(param, value)
            if rc != LpdDevice.ERROR_OK:
                self.msgPrint('Setting parameter %s failed (rc=%d) : %s' % (param, rc, self.device.errorStringGet()))
                self.deviceState = LpdFemGui.DeviceIdle
                return
            try:
                self.loadedConfig[param] = value
            except Exception as e:
                print >> sys.stderr, "%s" % e

        # Set up number of frames based on cached parameter value of number of trains
        self.numFrames = currentParams['numTrains']
        self.loadedConfig['numTrains'] = self.numFrames
        rc = self.device.paramSet('numberTrains', self.numFrames)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter femNumTestCycles failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return
        
        # Set up trigger source (internal vs external)
        externalTrigger = currentParams['externalTrigger']
        beamTriggerSource = 1 if externalTrigger == False else 0
        rc = self.device.paramSet('femStartTrainSource', beamTriggerSource)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter femBeamTriggerSource failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return
        
        # Set up external trigger delay
        triggerDelay = currentParams['triggerDelay']
        rc = self.device.paramSet('femStartTrainDelay', triggerDelay)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter femExternalTriggerStrobeDelay failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return

        # Set up pixel feedback override
        pixelFeedbackOverride = currentParams['femAsicPixelFeedbackOverride']
        rc = self.device.paramSet('femAsicPixelFeedbackOverride', pixelFeedbackOverride)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter femAsicPixelFeedbackOverride failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return

        # Set up ASIC gain mode override
        gainOverride = currentParams['femAsicGainOverride']
        rc = self.device.paramSet('femAsicGain', gainOverride)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter femAsicGainOverride failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return

        # Store values of data receiver address, port and number of frames
        try:
            self.dataListenAddr = self.loadedConfig['tenGig0DestIp']
            self.dataListenPort = self.loadedConfig['tenGig0DestPort']
        except Exception as e:
            print >> sys.stderr, "Got exception storing reaodut config variables", e 
        
        # Set ASIC setup parameters file
        self.msgPrint("Loading Setup Params from file %s" % currentParams['setupParamFile'])
        rc = self.device.paramSet('femAsicSetupParams', currentParams['setupParamFile'])
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting ASIC setup parameter file to %s failed (rc=%d) : %s" % 
                          (currentParams['setupParamFile'], rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return
            
        # Set ASIC command word sequence file
        self.msgPrint("Loading Command Seq from file %s" % currentParams['cmdSequenceFile'])
        rc = self.device.paramSet('femAsicCmdSequence', currentParams['cmdSequenceFile'])
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting ASIC command word sequence file to %s failed (rc=%d) : %s" % 
                          (currentParams['cmdSequenceFile'], rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return
        
        # Upload configuration parameters to device and configure system for acquisition    
        self.msgPrint("Uploading configuration to LPD FEM device...")
        rc = self.device.configure()
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Configuration upload failed (rc=%d) : %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return
        
        # Set device state as ready for acquisition        
        self.deviceState = LpdFemGui.DeviceReady
    
    def deviceRun(self, currentParams=None):
        
        # Open shutter - if selected
        if self.shutterEnabled:
            # Check shutter defined
            if self.shutter != 0:
                try:
                    self.shutter.move(1)
                    self.msgPrint("Wait a second for shutter to open..")
                    time.sleep(1)
                except Exception as e:
                    self.msgPrint(e)
            else:
                self.msgPrint("Error: Shutter undefined, check configurations file?")


        # if currentParams not supplied, use self.cachedParams
        if not currentParams:
            currentParams  = self.cachedParams

        # Increment the run number
        currentParams['runNumber'] = currentParams['runNumber'] + 1
        
        # Clear abort run flag
        self.abortRun = False

        # Launch LCLS EVR timestamp recorder thread if selected
        if currentParams['evrRecordEnable'] == True:
            try:
                timestampRecorder = LpdEvrTimestampRecorder(currentParams, self)
            except Exception as e:
                self.msgPrint("ERROR: failed to create timestamp recorder: %s" % e)
                self.deviceState = LpdFemGui.DevicdeIdle
                return
        
        # Create an LpdFemDataReceiver instance to launch readout threads
        try:
            dataReceiver = LpdFemDataReceiver(self.liveViewWindow.liveViewUpdateSignal, self.mainWindow.runStatusSignal,
                                              self.dataListenAddr, self.dataListenPort, self.numFrames, currentParams, self)
        except Exception as e:
            self.msgPrint("ERROR: failed to create data receiver: %s" % e)
            self.deviceState = LpdFemGui.DeviceIdle
            return
        
        # Set device state as running and trigger update of run state in GUI    
        self.deviceState = LpdFemGui.DeviceRunning
        self.runStateUpdate()        

        # Execute the run on the device
        rc = self.device.start()
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Acquisition start failed (rc=%d) : %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle

        # Wait for timestamp recorder thread to complete
        if currentParams['evrRecordEnable'] == True:
            try:
                timestampRecorder.awaitCompletion()
                dataReceiver.injectTimestampData(timestampRecorder.evrData)

            except Exception as e:
                self.msgPrint("ERROR: failed to complete EVR timestamp recorder: %s" % e)

        # Wait for the data receiver threads to complete
        try:
            dataReceiver.awaitCompletion()
            self.lastDataFile = dataReceiver.lastDataFile()
        except Exception as e:
            self.msgPrint("ERROR: failed to await completion of data receiver threads: %s" % e)
        
        # Close the shutter - if selected
        if self.shutterEnabled:
            # Check shutter defined
            if self.shutter != 0:
                try:
                    self.shutter.move(0)
                except Exception as e:
                    self.msgPrint(e)
            else:
                self.msgPrint("Error: Shutter undefined, check configurations file?")

        # Signal device state as ready
        self.deviceState = LpdFemGui.DeviceReady
        
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
    lpdFemGui = LpdFemGui(app)
    
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()
    
