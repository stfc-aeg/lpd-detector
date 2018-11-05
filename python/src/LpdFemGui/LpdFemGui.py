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

    def __init__(self, print_fn):
        self.print_fn = print_fn

    def write(self, text):
        if ord(text[0]) != 10:
            self.print_fn(text)

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
        self.default_config_path = os.getenv('LPD_FEM_GUI_CONFIG_PATH', os.getcwd() + '/config')

        # Load default parameters from persistent file store
        self.initialiseCachedParams()

        # Initialise device and default state
        self.device = LpdDevice()
        self.device_state = LpdFemGui.DeviceDisconnected
        self.device_err_string = ""
        self.fem_config = None

        self.data_listen_addr = '0.0.0.0'
        self.data_listen_port = 0
        self.num_frames      = 0

        self.last_data_file = None

        self.loaded_config   = {}
        
        self.odin_data_receiver = None

        # Create a power card manager instance
        self.pwr_card = LpdPowerCardManager(self, self.device)

        # Show/hide (ASIC) Testing tab?
        self.asic_testing_enabled = self.getCachedParam('asicTesting')
        
        # Should GUI itself receive fem data?
        self.receiveDataInternally = self.getCachedParam('receiveDataInternally')

        # Create the main window GUI and show it
        self.mainWindow = LpdFemGuiMainWindow(self)
        self.mainWindow.show()

        # Create the live view window but don't show it
        self.live_view_window = LpdFemGuiLiveViewWindow(asicModuleType=self.cached_params['asicModuleType'])

        if (self.asic_testing_enabled):
            try:
                # Create an LPD ASIC tester instance
                self.asic_tester = LpdAsicTester(self, self.device)

                self.asic_window = LpdFemGuiAsicWindow(self)
                self.asic_window.show()    # Hide window for now while testing

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
        self.abort_run = False

    def initialiseCachedParams(self):
        '''
        Initialises default parameters from JSON file-backed store, or creates them
        if not existing in file from coded defaults
        '''   
        self.param_cache_file = self.default_config_path + "/lpdFemGui_config.json"

        self.cached_params = PersistentDict(self.param_cache_file, 'c', format='json')

        default_params = { 'connectionTimeout' : 5.0,
                          'femAddr'           : '192.168.2.2',
                          'femPort'           : 6969,
                          'readoutParamFile'  : self.default_config_path + '/superModuleReadout.xml',
                          'cmdSequenceFile'   : self.default_config_path + '/Command_LongExposure_V2.xml',
                          'setupParamFile'    : self.default_config_path + '/Setup_LowPower.xml',
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
                          'receiveDataInternally': False,   # Data received either internally or from ODIN

                        'odinFrCtrlChannel'  : 'tcp://127.0.0.1:5000',
                        'odinFpCtrlChannel'  : 'tcp://127.0.0.1:5004',
                        # TODO: Plan file structure for odinDataConfigFile
                        'odinDataConfigFile' : self.default_config_path + '/odin_data_lpd_config.json',
                        'frameReceiverProcessorLocation' : '/u/xfu59478/develop/projects/lpd/install/bin'
                         }

        # List of parameter names that don't need to force a system reconfigure
        self.non_volatile_params = ('fileWriteEnable', 'liveViewEnable', 'liveViewDivisor', 'liveViewOffset',
                                  'pwrAutoUpdate', 'pwrUpdateInterval', 'dataFilePath', 'hvBiasBolts',
                                  'multiRunEnable', 'multiNumRuns')

        # Load default parameters into cache if not already existing        
        for param in default_params:
            if param not in self.cached_params:
                self.cached_params[param] = default_params[param]

        # Sync cached parameters back to file
        self.cached_params.sync()

    def getCachedParam(self, param):

        if param in self.cached_params:
            return self.cached_params[param]
        else:
            return None

    def setCachedParam(self, param, val):
        '''
        Update a cached parameter with a new value and flag that the device needs
        reconfiguring if the parameter is volatile
        '''
        if param not in self.cached_params or self.cached_params[param] != val:
            self.cached_params[param] = val
            self.cached_params.sync()
            if not param in self.non_volatile_params:
                if self.device_state == LpdFemGui.DeviceReady:
                    self.device_state = LpdFemGui.DeviceIdle

    def deviceConnect(self, address_str, port_str):

        rc = self.device.open(address_str, int(port_str), timeout=self.cached_params['connectionTimeout'],
                              asicModuleType=self.cached_params['asicModuleType'])
        if rc != LpdDevice.ERROR_OK:
            self.device_state = LpdFemGui.DeviceDisconnected
            self.device_err_string = "ERROR: connection failed: %s" % self.device.errorStringGet()
        else:
            self.device_state = LpdFemGui.DeviceIdle
            self.device_err_string = ""
            if (self.asic_testing_enabled):
                self.mainWindow.testTab.femConnectionSignal.emit(True)

    def deviceDisconnect(self):

        self.device.close()
        self.device_state = LpdFemGui.DeviceDisconnected
        if (self.asic_testing_enabled):
            self.mainWindow.testTab.femConnectionSignal.emit(False)

    def cleanup(self):

        self.cached_params.sync()

    def femConfigGet(self):

        if self.device_state != LpdFemGui.DeviceDisconnected:
            self.fem_config = self.device.femClient.configRead()

    def femConfigUpdate(self, net_mac, net_ip, net_mask, 
                        net_gw, temp_high, temp_crit, 
                        sw_major, sw_minor, fw_major, fw_minor,
                        hw_major, hw_minor, board_id, board_type):

        the_config = FemConfig(net_mac, net_ip, net_mask, 
                        net_gw, temp_high, temp_crit, 
                        sw_major, sw_minor, fw_major, fw_minor,
                        hw_major, hw_minor, board_id, board_type)

        if self.device_state != LpdFemGui.DeviceDisconnected:        
            self.device.femClient.configWrite(the_config)

    def deviceConfigure(self, current_params=None):

        self.device_state = LpdFemGui.DeviceConfiguring
        self.runStateUpdate()

        try:        
            # if current_params not supplied, use self.cached_params
            if not current_params:
                current_params  = self.cached_params

        except Exception as e:
            print("\ndeviceConfigure Exception: %s doesn't exist?" % e, file=sys.stderr)

        try:
            self.shutterEnabled = current_params['arduinoShutterEnable']
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
        self.loaded_config= {}

        # Load readout parameters from file       
        self.msgPrint("Loading Readout Params from file %s" % current_params['readoutParamFile'])
        try:
            readout_config = LpdReadoutConfig(current_params['readoutParamFile'], fromFile=True)
        except LpdReadoutConfigError as e:
            self.msgPrint("Error loading readout parameters: %s" % e)
            self.device_state = LpdFemGui.DeviceIdle
            return

        # Set all parameters from file on device
        for (param, value) in readout_config.parameters():
            rc = self.device.paramSet(param, value)
            if rc != LpdDevice.ERROR_OK:
                self.msgPrint('Setting parameter %s failed (rc=%d) : %s' % (param, rc, self.device.errorStringGet()))
                self.device_state = LpdFemGui.DeviceIdle
                return
            try:
                self.loaded_config[param] = value
            except Exception as e:
                print("%s" % e, file=sys.stderr)

        # Set up pixel feedback override
        pixel_feedback_override = current_params['femAsicPixelFeedbackOverride']
        rc = self.device.paramSet('femAsicPixelFeedbackOverride', pixel_feedback_override)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter femAsicPixelFeedbackOverride failed (rc=%d) %s" % 
                          (rc, self.device.errorStringGet()))
            self.device_state = LpdFemGui.DeviceIdle
            return

        # Store values of data receiver address, port and number of frames
        try:
            self.data_listen_addr = self.loaded_config['tenGig0DestIp']
            self.data_listen_port = self.loaded_config['tenGig0DestPort']
        except Exception as e:
            print("Got exception, missing XML config variable", e, file=sys.stderr) 

        # Set ASIC setup parameters file
        self.msgPrint("Loading Setup Params from file %s" % current_params['setupParamFile'])
        rc = self.device.paramSet('femAsicSetupParams', current_params['setupParamFile'])
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting ASIC setup parameter file to %s failed (rc=%d) : %s" % 
                          (current_params['setupParamFile'], rc, self.device.errorStringGet()))
            self.device_state = LpdFemGui.DeviceIdle
            return

        # Set ASIC command word sequence file
        self.msgPrint("Loading Command Seq from file %s" % current_params['cmdSequenceFile'])
        rc = self.device.paramSet('femAsicCmdSequence', current_params['cmdSequenceFile'])
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting ASIC command word sequence file to %s failed (rc=%d) : %s" % 
                          (current_params['cmdSequenceFile'], rc, self.device.errorStringGet()))
            self.device_state = LpdFemGui.DeviceIdle
            return

        # Upload configuration parameters to device and configure system for acquisition
        self.msgPrint("Uploading configuration to LPD FEM device...")
        rc = self.device.configure()
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Configuration upload failed (rc=%d) : %s" % (rc, self.device.errorStringGet()))
            self.device_state = LpdFemGui.DeviceIdle
            return

        # Set device state as ready for acquisition
        self.device_state = LpdFemGui.DeviceReady

    def deviceQuickConfigure(self, trigger_delay_increment_modifier):

        self.device_state = LpdFemGui.DeviceConfiguring
        self.runStateUpdate()

        # Set up external trigger delay
        triggerDelay = self.cached_params['triggerDelay'] + trigger_delay_increment_modifier
        rc = self.device.paramSet('femStartTrainDelay', triggerDelay)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter femStartTrainDelay failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.device_state = LpdFemGui.DeviceIdle
            return

        # Set up ASIC gain mode override
        gainOverride = self.cached_params['femAsicGainOverride']
        rc = self.device.paramSet('femAsicGain', gainOverride)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter femAsicGainOverride failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.device_state = LpdFemGui.DeviceIdle
            return

        # Set up number of frames based on cached parameter value of number of trains
        self.num_frames = self.cached_params['numTrains']
        self.loaded_config['numTrains'] = self.num_frames
        rc = self.device.paramSet('numberTrains', self.num_frames)
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Setting parameter numberTrains failed (rc=%d) %s" % (rc, self.device.errorStringGet()))
            self.device_state = LpdFemGui.DeviceIdle
            return

        # Do quick configure on FEM    
        self.msgPrint("Doing quick configuration...")
        rc = self.device.quick_configure()
        if rc != LpdDevice.ERROR_OK:
            self.msgPrint("Quick configure failed (rc=%d) : %s" % (rc, self.device.errorStringGet()))
            self.device_state = LpdFemGui.DeviceIdle
            return

        # Set device state as ready for acquisition        
        self.device_state = LpdFemGui.DeviceReady

    def deviceRun(self, current_params=None):

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


        # if current_params not supplied, use self.cached_params
        if not current_params:
            current_params  = self.cached_params

        # Clear abort run flag
        self.abort_run = False

        # Set up number of runs based on multi-run enable flag
        num_runs = 1
        if current_params['multiRunEnable']:
            num_runs = current_params['multiRunNumRuns']
            self.msgPrint("Multiple runs enabled: executing %d runs" % num_runs)

        for run in range(num_runs):

            if num_runs > 1:
                self.msgPrint("Starting run %d of %d ..." % (run+1, num_runs))

            # Increment the run number
            current_params['runNumber'] = current_params['runNumber'] + 1
        
            # Enable multi-run, scanning through range of trigger delays
            triggerDelayIncrement = self.cached_params['triggerDelayIncrement']
            trigger_delay_increment_modifier = triggerDelayIncrement * run

            # Do quick configure before run
            self.deviceQuickConfigure(trigger_delay_increment_modifier)

            # Launch LCLS EVR timestamp recorder thread if selected
            if current_params['evrRecordEnable'] == True:
                try:
                    timestamp_recorder = LpdEvrTimestampRecorder(current_params, self)
                except Exception as e:
                    self.msgPrint("ERROR: failed to create timestamp recorder: %s" % e)
                    self.device_state = LpdFemGui.DevicdeIdle
                    return

#-------------------------------------------------------------
            if self.receiveDataInternally:
                # Create an LpdFemDataReceiver instance to launch readout threads
                try:
                    data_receiver = LpdFemDataReceiver(self.live_view_window.liveViewUpdateSignal, self.mainWindow.run_status_signal,
                                                      self.data_listen_addr, self.data_listen_port, self.num_frames, current_params, self)
                except Exception as e:
                    self.msgPrint("ERROR: failed to create data receiver: %s" % e)
                    self.device_state = LpdFemGui.DeviceIdle
                    return
            else:
                # Launch ODIN LPD Frame Receiver, Proccesor and Data Monitor using ODIN data
                try:
                    # One-off configuration per session
                    if self.odin_data_receiver is None:
                        self.odin_data_receiver = LpdFemOdinDataReceiver(self.mainWindow.run_status_signal, self.num_frames, self)
                    
                    num_frames = self.getCachedParam('numTrains')
                    num_images = self.loaded_config['numberImages']
                    
                    # Configuration for every run
                    self.odin_data_receiver.configure(num_frames, num_images)
                except Exception as e:
                    self.msgPrint("ERROR: failed to create/configure ODIN data receiver: %s" % e)
                    self.device_state = LpdFemGui.DeviceIdle
                    return
#-------------------------------------------------------------

            # Set device state as running and trigger update of run state in GUI
            self.device_state = LpdFemGui.DeviceRunning
            self.runStateUpdate()

            # Execute the run on the device
            rc = self.device.start()
            if rc != LpdDevice.ERROR_OK:
                self.msgPrint("Acquisition start failed (rc=%d) : %s" % (rc, self.device.errorStringGet()))
                self.device_state = LpdFemGui.DeviceIdle

            # Last iteration of loop? Close shutter as all runs now completed
            if run == (num_runs -1):
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
            if current_params['evrRecordEnable'] == True:
                try:
                    timestamp_recorder.awaitCompletion()
                    if self.receiveDataInternally:
                        data_receiver.injectTimestampData(timestamp_recorder.evr_data)
                    else:   # Receiving data from ODIN
                        self.odin_data_receiver.injectTimestampData(timestamp_recorder.evr_data)
#------------------------------------------------------------------------------------
                except Exception as e:
                    self.msgPrint("ERROR: failed to complete EVR timestamp recorder: %s" % e)

            if self.receiveDataInternally:
                # Wait for the data receiver threads to complete
                try:
                    data_receiver.awaitCompletion()
                    self.last_data_file = data_receiver.last_data_file()
                except Exception as e:
                    self.msgPrint("ERROR: failed to await completion of data receiver threads: %s" % e)

                # Delete dataReceiver or multi-run produces no data for even runs
                del data_receiver
            else:
                # Wait for the data receiver threads to complete
                try:
                    self.odin_data_receiver.awaitCompletion()
                except Exception as e:
                    self.msgPrint("ERROR: failed to await completion of data receiver threads: %s" % e)
#---------------------

            if num_runs > 1 and self.abort_run:
                self.msgPrint("Aborting multi-run sequence after {} runs".format(run+1))
                break

        # Closing Shutter code just to sit here (it's now in the above loop)

        # Signal device state as ready
        self.device_state = LpdFemGui.DeviceReady
        
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
    try:
        app = QtGui.QApplication(sys.argv)
        lpd_fem_gui = LpdFemGui(app)

        sys.exit(app.exec_())
    finally:
        if lpd_fem_gui.odin_data_receiver is not None:
            lpd_fem_gui.odin_data_receiver.shutdown_frame_receiver_processor()

if __name__ == '__main__':
    main()
