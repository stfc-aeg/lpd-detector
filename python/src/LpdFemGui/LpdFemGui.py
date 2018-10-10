from __future__ import print_function
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

#-----
from odin_data.ipc_channel import IpcChannel, IpcChannelException
from odin_data.ipc_message import IpcMessage, IpcMessageException
from LpdFemOdinDataReceiver import *
#-----

class PrintRedirector():

    def __init__(self, printFn):
        self.printFn = printFn

    def write(self, text):
        if ord(text[0]) != 10:
            self.printFn(text)

    def flush(self):
        print("PrintRedirector now has a flush() function..")

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
        
        self.odinDataReceiver = None

        # Create a power card manager instance
        self.pwrCard = LpdPowerCardManager(self, self.device)

        # Show/hide (ASIC) Testing tab?
        self.asicTestingEnabled = self.getCachedParam('asicTesting')
        
        # Should GUI itself receive fem data?
        self.receiveDataInternally = self.getCachedParam('receiveDataInternally')

#-----
        # Should ODIN receive fem data?
        self.receiveDataFromODIN = self.getCachedParam('receiveDataFromODIN')
#-----

        # Create the main window GUI and show it
        self.mainWindow= LpdFemGuiMainWindow(self)
        self.mainWindow.show()

        # Create the live view window but don't show it
        self.liveViewWindow = LpdFemGuiLiveViewWindow(asicModuleType=self.cachedParams['asicModuleType'])

        if (self.asicTestingEnabled):
            try:
                # Create an LPD ASIC tester instance
                self.asicTester = LpdAsicTester(self, self.device)

                self.asicWindow = LpdFemGuiAsicWindow(self)
                self.asicWindow.show()    # Hide window for now while testing

            except Exception as e:
                print("LpdFemGui initialisation exception: %s" % e, file=sys.stderr)

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
                self.shutter.move(b'\0')
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
                          'multiRunEnable'    : True,
                          'multiRunNumRuns'   : 123,
                          'receiveDataInternally': False,   # This should be set to false when receiveDataFromODIN is true
#-----
                        'receiveDataFromODIN': True,
                        'odinFrCtrlChannel'  : 'tcp://127.0.0.1:5000',
                        'odinFpCtrlChannel'  : 'tcp://127.0.0.1:5004',
                        # TODO: Plan file structure for odinDataConfigFile
                        'odinDataConfigFile' : self.defaultConfigPath + '/odin_data_lpd_config.json',
#-----
                         }

        # List of parameter names that don't need to force a system reconfigure
        self.nonVolatileParams = ('fileWriteEnable', 'liveViewEnable', 'liveViewDivisor', 'liveViewOffset',
                                  'pwrAutoUpdate', 'pwrUpdateInterval', 'dataFilePath', 'hvBiasBolts',
                                  'multiRunEnable', 'multiNumRuns')

        # Load default parameters into cache if not already existing        
        for param in defaultParams:
            if param not in self.cachedParams:
                self.cachedParams[param] = defaultParams[param]

        # Sync cached parameters back to file
        self.cachedParams.sync()

    def getCachedParam(self, param):

        if param in self.cachedParams:
            return self.cachedParams[param]
        else:
            return None

    def setCachedParam(self, param, val):
        '''
        Update a cached parameter with a new value and flag that the device needs
        reconfiguring if the parameter is volatile
        '''
        if param not in self.cachedParams or self.cachedParams[param] != val:
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
            if (self.asicTestingEnabled):
                self.mainWindow.testTab.femConnectionSignal.emit(True)

    def deviceDisconnect(self):

        self.device.close()
        self.deviceState = LpdFemGui.DeviceDisconnected
        if (self.asicTestingEnabled):
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
            print("\ndeviceConfigure Exception: %s doesn't exist?" % e, file=sys.stderr)

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
                        self.shutter.move(b'\0')
                    except Exception as e:
                        self.msgPrint("Shutter %s" % e)
            else:
                if self.shutter != 0:
                    # Close serial connection
                    self.shutter.__del__()
                    self.shutter = 0
        except Exception as e:
            print("configurable issues: ", e, file=sys.stderr)

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
                print("%s" % e, file=sys.stderr)

        # Set up pixel feedback override
        pixelFeedbackOverride = currentParams['femAsicPixelFeedbackOverride']
        rc = self.device.paramSet('femAsicPixelFeedbackOverride', pixelFeedbackOverride)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter femAsicPixelFeedbackOverride failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return

        # Store values of data receiver address, port and number of frames
        try:
            self.dataListenAddr = self.loadedConfig['tenGig0DestIp']
            self.dataListenPort = self.loadedConfig['tenGig0DestPort']
        except Exception as e:
            print("Got exception, missing XML config variable", e, file=sys.stderr) 

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

    def deviceQuickConfigure(self, triggerDelayIncrementModifier):

        self.deviceState = LpdFemGui.DeviceConfiguring
        self.runStateUpdate()

        # Set up external trigger delay
        triggerDelay = self.cachedParams['triggerDelay'] + triggerDelayIncrementModifier
        rc = self.device.paramSet('femStartTrainDelay', triggerDelay)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter femStartTrainDelay failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return

        # Set up ASIC gain mode override
        gainOverride = self.cachedParams['femAsicGainOverride']
        rc = self.device.paramSet('femAsicGain', gainOverride)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter femAsicGainOverride failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return

        # Set up number of frames based on cached parameter value of number of trains
        self.numFrames = self.cachedParams['numTrains']
        self.loadedConfig['numTrains'] = self.numFrames
        rc = self.device.paramSet('numberTrains', self.numFrames)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter numberTrains failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.deviceState = LpdFemGui.DeviceIdle
            return

        # Do quick configure on FEM    
        self.msgPrint("Doing quick configuration...")
        rc = self.device.quick_configure()
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Quick configure failed (rc=%d) : %s" % (rc, self.device.errorStringGet()))
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
                    self.shutter.move(b'\1')
                    self.msgPrint("Wait a second for shutter to open..")
                    time.sleep(1)
                except Exception as e:
                    self.msgPrint(e)
            else:
                self.msgPrint("Error: Shutter undefined, check configurations file?")


        # if currentParams not supplied, use self.cachedParams
        if not currentParams:
            currentParams  = self.cachedParams

        # Clear abort run flag
        self.abortRun = False

        # Set up number of runs based on multi-run enable flag
        numRuns = 1
        if currentParams['multiRunEnable']:
            numRuns = currentParams['multiRunNumRuns']
            self.msgPrint("Multiple runs enabled: executing %d runs" % numRuns)

        for run in range(numRuns):

            if numRuns > 1:
                self.msgPrint("Starting run %d of %d ..." % (run+1, numRuns))

            # Increment the run number
            currentParams['runNumber'] = currentParams['runNumber'] + 1
        
            # Enable multi-run, scanning through range of trigger delays
            triggerDelayIncrement = self.cachedParams['triggerDelayIncrement']
            triggerDelayIncrementModifier = triggerDelayIncrement * run

            # Do quick configure before run
            self.deviceQuickConfigure(triggerDelayIncrementModifier)

            # Launch LCLS EVR timestamp recorder thread if selected
            if currentParams['evrRecordEnable'] == True:
                try:
                    timestampRecorder = LpdEvrTimestampRecorder(currentParams, self)
                except Exception as e:
                    self.msgPrint("ERROR: failed to create timestamp recorder: %s" % e)
                    self.deviceState = LpdFemGui.DevicdeIdle
                    return

            if self.receiveDataInternally:
                # Create an LpdFemDataReceiver instance to launch readout threads
                try:
                    dataReceiver = LpdFemDataReceiver(self.liveViewWindow.liveViewUpdateSignal, self.mainWindow.runStatusSignal,
                                                      self.dataListenAddr, self.dataListenPort, self.numFrames, currentParams, self)
                except Exception as e:
                    self.msgPrint("ERROR: failed to create data receiver: %s" % e)
                    self.deviceState = LpdFemGui.DeviceIdle
                    return

#-------------------------------------------------------------
            if self.receiveDataFromODIN:
                # Launch ODIN LPD Frame Receiver, Proccesor and Data Monitor
                try:
                    if self.odinDataReceiver is None:
                        self.odinDataReceiver = LpdFemOdinDataReceiver(self.mainWindow.runStatusSignal,self.numFrames, self)
                    
                    num_frames = self.getCachedParam('numTrains')
                    num_images = self.loadedConfig['numberImages']
                    self.odinDataReceiver.configure(num_frames, num_images)
                except Exception as e:
                    self.msgPrint("ERROR: failed to create/configure ODIN data receiver: %s" % e)
                    self.deviceState = LpdFemGui.DeviceIdle
                    return
#-------------------------------------------------------------

            # Set device state as running and trigger update of run state in GUI
            self.deviceState = LpdFemGui.DeviceRunning
            self.runStateUpdate()

            # Execute the run on the device
            rc = self.device.start()
            if rc != LpdDevice.ERROR_OK:
                self.msgPrint("Acquisition start failed (rc=%d) : %s" % (rc, self.device.errorStringGet()))
                self.deviceState = LpdFemGui.DeviceIdle

            # Last iteration of loop? Close shutter as all runs now completed
            if run == (numRuns-1):
                # Close the shutter - if selected
                if self.shutterEnabled:
                    # Check shutter defined
                    if self.shutter != 0:
                        try:
                            self.shutter.move(b'\0')
                        except Exception as e:
                            self.msgPrint(e)
                    else:
                        self.msgPrint("Error: Shutter undefined, check configurations file?")

            # Wait for timestamp recorder thread to complete
            if currentParams['evrRecordEnable'] == True:
                try:
                    timestampRecorder.awaitCompletion()
                    if self.receiveDataInternally:
                        dataReceiver.injectTimestampData(timestampRecorder.evrData)
#------------------------------------------------------------------------------------
                    if self.receiveDataFromODIN:
                        self.odinDataReceiver.injectTimestampData(timestampRecorder.evrData)
#------------------------------------------------------------------------------------
                except Exception as e:
                    self.msgPrint("ERROR: failed to complete EVR timestamp recorder: %s" % e)

            if self.receiveDataInternally:
                # Wait for the data receiver threads to complete
                try:
                    dataReceiver.awaitCompletion()
                    self.lastDataFile = dataReceiver.lastDataFile()
                except Exception as e:
                    self.msgPrint("ERROR: failed to await completion of data receiver threads: %s" % e)

                # Delete dataReceiver or multi-run produces no data for even runs
                del dataReceiver

#------------------
            if self.receiveDataFromODIN:
                # Wait for the data receiver threads to complete
                try:
                    self.odinDataReceiver.awaitCompletion()
                except Exception as e:
                    self.msgPrint("ERROR: failed to await completion of data receiver threads: %s" % e)
#---------------------

            if numRuns > 1 and self.abortRun:
                self.msgPrint("Aborting multi-run sequence after {} runs".format(run+1))
                break

        # Closing Shutter code just to sit here (it's now in the above loop)

        # Signal device state as ready
        self.deviceState = LpdFemGui.DeviceReady
        
    def msgPrint(self, message):
        '''
        Sends a message to the GUI thread for display
        '''
        self.mainWindow.messageSignal.emit(message)
        
    def runStateUpdate(self):
        '''return
        Sends a run state update to the GUI thread for display
        ''' 
        self.mainWindow.runStateSignal.emit()

def main():

    app = QtGui.QApplication(sys.argv)  
    lpdFemGui = LpdFemGui(app)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
