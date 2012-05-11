'''
Created on 21 Oct 2011

@author: ckd27546
'''

from excaliburPowerGuiMain import ExcaliburPowerGuiMain

import sys, threading, Queue, time
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QString
#from QtGui import QFileDialog
import serial
from time import strftime       # Used for creating name of log file

# Defined exceptions
class OutOfRangeError(Exception): pass
class BadArgumentError(Exception): pass
class ArgumentTypeNoneError(Exception): pass
class MalformedStringError(Exception): pass
class WrongVariableType(Exception): pass


class ExcaliburPowerGui:
    """
    Launch the main part of the GUI and the worker thread. periodicCall and
    endApplication could reside in the GUI part, but putting them here
    means all thread controls in a single place.
    """
    def __init__(self, app, bUnitTest=False):

        self.app = app
        self.bTest = bUnitTest
        
        # Defined thresholds for the four status quantities
        self.humidityMin = 17 #60
        self.humidityMax = 30 #80
        self.humidityWarn = 3
        self.airTempMin = 10
        self.airTempMax = 50
        self.coolantFlowMin = 5
        self.coolantFlowMax = 10
        self.coolantTempMin = 2
        self.coolantTempMax = 10

        # Boolean variables tracking whether LEDs are green (True) or red (False)
        self.bHumidityGreen = False
        self.bAirTempGreen = False
        self.bCoolantFlowGreen = False
        self.bCoolantTempGreen = False
        self.bLvGreen = False
        self.bBiasGreen = False

        # Boolean True: Log header, False: Log Gui values
        self.bInitialisation = True     # I2C devices initialisation period while True
        self.bLogHeader = True          # Log header information to log file when True
        self.bPauseTimers = False       # Prevents timers doing anything while True

        # Temporarily: Used by biasButton and lvButton to toggle associated "LEDs"
        self.bBiasEnabled = False
        self.bLvEnabled = False
        
        # Create the queue
        self.queue = Queue.Queue()
        
        # Set up the GUI part
        self.gui = ExcaliburPowerGuiMain(self.queue, self.endApplication)        

        # bUnitTest = true, only during Unit Test
        if self.bTest is True:
            # Make GUI visible, but skip the rest as not necessary for unit testing
            self.gui.show()
        else:
            # Make a list of available com ports
            self.availableComPorts = scanSerialPorts()
            # Populate QListWidget with COM ports
            for comNo,comStr in self.availableComPorts:
                # Populate QListWidget with COM ports
                item1 = QtGui.QListWidgetItem()
                item1.setText( QtGui.QApplication.translate("mainWindow", comStr, None, QtGui.QApplication.UnicodeUTF8))
                self.gui.gui.lwSerialPort.addItem(item1)

            # Ensure Debug components disabled from start..
            self.toggleDebugComponents(False)
            # Make GUI visible
            self.gui.show()

            # Track whether CbPollingBox is ticked (True), or unticked (False)
            self.bPollingEnabled = False
            
            # Manual port selection (true), or automatic selection (false)
            ''' True = Manually choose port, False = Automatic selection '''
            self.bManual = False
            
            # Open serial port
            if self.bManual is False:
                # Hardcoded:
                self.sCom = serial.Serial(port=2, baudrate = 57600, timeout = 1)
                # Disable list of COM ports
                self.gui.gui.lwSerialPort.setEnabled(False)
                # Tick polling option
                self.gui.gui.cbPollingBox.setChecked(True)
                self.bPollingEnabled = True
                # Make sure lv and bias LEDs look green
                self.lvButtonAction()
                self.biasButtonAction()
                self.gui.gui.biasButton.setEnabled(False)
            else:
                # Using GUI selection
                self.sCom = False
                # Untick polling option
                self.gui.gui.cbPollingBox.setChecked(False)
                self.bPollingEnabled = False
                # Disable
                self.gui.gui.leBiasLevel.setEnabled(False)
                self.gui.gui.lvButton.setEnabled(False)
                self.gui.gui.biasButton.setEnabled(False)
                self.gui.gui.selectButton.setEnabled(False)
                self.gui.gui.leSelectLogFileLocation.setEnabled(False)
                # Disable polling until user has selected com port and file name
                self.gui.gui.cbPollingBox.setEnabled(False)
                
            if self.bManual is False:
                # Call function to create status bar
                self.createStatusBar("Initialising ...")
                # Show progress bar and animate it
                self.gui.progressBar.show()
                self.gui.progressBar.setRange(0, 0)

            # Define how often we poll devices during polling mode
            self.pollingInterval = float(self.gui.gui.lePollingInterval.text())/1000
            
            # A timer to periodically call periodicCall :-)
            self.periodicTimer = QtCore.QTimer()
            QtCore.QObject.connect(self.periodicTimer,
                               QtCore.SIGNAL("timeout()"),
                               self.periodicCall)

            # Use timer to log values from gui to file
            self.logTimer = QtCore.QTimer()
            QtCore.QObject.connect(self.logTimer,
                                   QtCore.SIGNAL("timeout()"),
                                   self.periodicLog )
            # Connect debugButton to call function debugSend
            QtCore.QObject.connect(self.gui.gui.debugButton,
                                   QtCore.SIGNAL("clicked()"), 
                                   self.debugSend)
            # Call function lwSerialPortChosen() when COM port chosen
            QtCore.QObject.connect(self.gui.gui.lwSerialPort,
                                   QtCore.SIGNAL("itemSelectionChanged()"),
                                   self.lwSerialPortChosen)
            # Call function biasButtonAction() when biasButton is pressed
            QtCore.QObject.connect(self.gui.gui.biasButton,
                                   QtCore.SIGNAL("clicked()"),
                                   self.biasButtonAction)
            # Call function lvButtonAction() when lvButton is pressed
            QtCore.QObject.connect(self.gui.gui.lvButton,
                                   QtCore.SIGNAL("clicked()"),
                                   self.lvButtonAction)
            # Call function logPollingStatus whenever polling checkbox clicked
            QtCore.QObject.connect(self.gui.gui.cbPollingBox,
                                   QtCore.SIGNAL("clicked()"),
                                   self.logPollingStatus)
            # Call function selectButtonAction when selectButton is pressed
            QtCore.QObject.connect(self.gui.gui.selectButton,
                                   QtCore.SIGNAL("clicked()"),
                                   self.selectButtonAction)
            # Start the timer -- this replaces the initial call to periodicCall
            self.periodicTimer.start(100)
            # Don't start logTimer until all devices ready (i.e. inside WorkerThread1)
            self.logTimer.start(1000)

            # Construct default log filename, folder and absolute path
            self.logFileName = strftime("%Y-%m-%d_%H%M%S_GuiLog.log")
            self.logFolderName = str(QtCore.QDir.currentPath())
            # Construct absolute file path, e.g. "C:\temp\fileName.log"
            self.currentLogFile = self.logFolderName + "/" + self.logFileName
            self.gui.gui.leSelectLogFileLocation.setText(  self.currentLogFile)            
                        
            # Set up the thread to do asynchronous I/O
            self.running = 1
            self.thread1 = threading.Thread(target=self.workerThread1)
            self.thread1.start()
            
    def periodicCall(self):
        """ Check every 100 ms if there is something new in the queue
            for the GUI side to process """
        # Do not log file timers are "paused"
        if self.bPauseTimers is False:
            self.gui.processIncoming()
        if not self.running:
            self.app.quit()
            
    def selectButtonAction(self):
        """ Open QFileDialog to select folder and file name when selectButton pressed """        
        
        filename = (QtGui.QFileDialog.getSaveFileName( parent=None, 
                                                       caption = "Select Log file: Destination folder and Filename", 
                                                       directory = QString(), filter = "Log files (*.log *.csv)") )
        filename = str(filename)
        if filename.__len__() is not 0: # Only act if user specified a filename
            # Compare new choice with existing farming 
            if self.currentLogFile == filename:
                # Same filename specified, do nothing
#                print "Same filename specified, returning.."
                return
            else:
                # New file specified; Close existing file object in self.file
                try:
                    self.file.close()
                except AttributeError:
                    print "self.file does not already exist"
                # self.file now closed, update self.currentLogFile with filename
                self.currentLogFile = filename
                self.gui.gui.leSelectLogFileLocation.setText( self.currentLogFile )
                # Set self.bLogHeader = True to so periodicLog() writes header info
                self.bLogHeader = True
                # Temporarily enable boolean to enable logging header info
                self.bPauseTimers = False
                self.periodicLog()
                self.bPauseTimers = True                
        
    def endApplication(self):
        """ Signal to workerThread1 to stop, then close serial port """
        # Close file object unless doing unit testing
        if self.bTest is False:
            try:
                self.file.close()   # If self.file doesn't exist, will throw AttributeError
            except AttributeError:
                pass            # No action required
        self.running = 0
        # Only close serial port if it's open
        if self.sCom is not False:
            self.sCom.close()
        
    def workerThread1(self):
        """ This is where we handle the asynchronous I/O. """
        # Do nothing if serial port selected through GUI
        while self.sCom is False and (self.running is 1):
            pass
        # Print selected com port:    (e.g. COM1)
#        print self.gui.gui.lwSerialPort.currentItem().text()
        # Disable list of COM ports if port selected manually
        if self.bManual is True:
            self.gui.gui.lwSerialPort.setEnabled(False)
            # Wait until bias is enabled before continuing
            while self.gui.gui.biasButton.isEnabled() is False:
                pass
        time.sleep(2)        
        # Wait for serial interface to initialise.
        time.sleep(1.8)        # Redundant later on?
        # Initialise i2c devices
        if self.sCom:
            self.initialiseCommunication()
        if self.bManual is False:    
            # Signal to GUI: hide progressBar and statusBar components
            self.queue.put("hideGuiBars=...")
        while self.running:
            #This is where we poll the Serial port. 
            # Do not proceed unless polling checkbox ticked:
            if self.gui.gui.cbPollingBox.isChecked() == False:#is False:
                # Polling's disabled, ensure Debug & Select File components enabled
                self.toggleDebugComponents(True)
                self.toggleSelectFileComponents(True)
                # Pause timers until polling re-enabled
                self.bPauseTimers = True
                # Wait 150 ms before checking if polling ticked again
                time.sleep(0.150)
                continue
            else:
                # Polling's enabled, ensure Debug & Select File components disabled
                self.toggleDebugComponents(False)
                self.toggleSelectFileComponents(False)
                # Resume timers
                self.bPauseTimers = False                
                # Update polling interval in case it's been changed
                self.pollingInterval = float(self.gui.gui.lePollingInterval.text())/1000
            # polling enabled, wait then poll all devices:
            try:
                self.doEventHandler()
                time.sleep(self.pollingInterval)
            except:
                self.displayErrorMessage("workerThread1: doEventHandler() exception: ")

    def periodicLog(self):
        """ Log Gui values periodically """
        # Only log if not unit testing
        if self.bTest is False:
            # Do not log wild timers are "paused"
            if self.bPauseTimers is False:
                # Don't log while i2c initialising
                if self.bInitialisation is False:
    
                    if self.bLogHeader is True:
                        # Create and write header first time only
                        self.bLogHeader = False
                        # Construct log file's header
                        header = (strftime("%Y-%m-%d, %H:%M:%S, ") +
                                  self.gui.gui.lbl5V_A.text() + ", " + self.gui.gui.lbl5V_B.text() + ", " + self.gui.gui.lbl5VF0.text() + ", " + 
                                  self.gui.gui.lbl5VF1.text() + ", " + self.gui.gui.lbl5VF2.text() + ", " + self.gui.gui.lbl5VF3.text() + ", " + 
                                  self.gui.gui.lbl5VF4.text() + ", " + self.gui.gui.lbl5VF5.text() + ", " + self.gui.gui.lblHum_mon.text() + ", " +
                                  self.gui.gui.lblHum_stat.text() + ",\n")
                        # Create log file
                        self.file = open( self.currentLogFile, 'w')
                        self.file.write(header)
                    else:
                        # Only log data while polling
                        if self.gui.gui.cbPollingBox.isChecked() is True:
                            # Log Gui values to file
                            self.logCurrentValues()

    def logPollingStatus(self):
        """ Log polling status whenever cbPollingBox checkbox clicked """
        # Is cbPollingBox enabled?
        if self.gui.gui.cbPollingBox.isChecked() is True:
            # Polling just enabled, Enable biasButton if serial port manually chosen
            if self.bManual is True:
                self.gui.gui.biasButton.setEnabled(False)                
        else:
            # Polling just disabled, Disable biasButton if serial port manually chosen
            if self.bManual is True:
                self.gui.gui.biasButton.setEnabled(True)
        # Check whether file object exists in self.file
        try:
            if self.file.closed is True:
                # File object exists but is closed, do not log
                print "File object closed, will not log."
                return
            else:
                # File object exists and it's open: log change of Polling
#                print "File object open, logging.."
                # Construct current timestamp, append current polling status
                logString = (strftime("%Y-%m-%d, %H:%M:%S, "))
                if self.gui.gui.cbPollingBox.isChecked() is True:
                    logString = logString + "Polling Enabled\n"
                else:
                    logString = logString + "Polling Disabled\n"
                self.file.write(logString)
        except AttributeError:
            pass                # No action required
#            print "self.file file object doesn't exist"
            
    def msgPrint(self, msg, term='\n'):
        """ Put msg (error) string into mbErrorMessages (TextField) """
#        if msg is None:
        if compareTypes(msg) is not 3:
            raise BadArgumentError, "msgPrint() Error: argument not string!"            
        else:
            self.gui.gui.mbErrorMessages.insertPlainText(str(msg) + term)
            self.app.processEvents()
            return True
        
    def logCurrentValues(self):
        """ Write all current Gui values to string and write that to log file """
        data = (strftime("%Y-%m-%d, %H:%M:%S, ") + 
                self.gui.gui.le5VAV.text() + ", " + self.gui.gui.le5VBV.text() + ", " + self.gui.gui.le5F0I.text() + ", " + 
                self.gui.gui.le5F1I.text() + ", " + self.gui.gui.le5F2I.text() + ", " + self.gui.gui.le5F3I.text() + ", " + 
                self.gui.gui.le5F4I.text() + ", " + self.gui.gui.le5F5I.text() + ", " + self.gui.gui.leHum_mon.text() + ", " +
                self.gui.gui.leAirtmp_mon.text() + ",\n")
        try:
            self.file.write(data)
        except:
            print "logCurrentValues: Unable to log data"

    def logError(self, msgError):
        """ Write msgError to log file """
#        if msgError is None:
        if compareTypes(msgError) is not 3:
            raise BadArgumentError, "logError() Error, msgError argument not string!"
        else:
            # Unit testing only: return True if argument testing successful
            if self.bTest is True:
                return True
            # Check self.file still open
            if self.file.closed is False:
                data = (strftime("%Y-%m-%d, %H:%M:%S, ") + "Error: " + 
                        str(msgError) + ",\n")
                self.file.write(data)
            else:
                print "logError() didn't log, self.file file object closed."

    def createStatusBar(self, defaultMessage=""):
        """ Create a status bar in the bottom right corner """
        sb = QtGui.QStatusBar()
        sb.setFixedHeight(26)        
        self.gui.setStatusBar(sb)
        sb.showMessage(str(defaultMessage))
        self.gui.progressBar = QtGui.QProgressBar(self.gui.statusBar())
        self.gui.statusBar().addPermanentWidget(self.gui.progressBar, 0)
        self.gui.progressBar.hide()

    def debugSend(self):
        """ Executes each time debugButton is pressed """
        # Get string from debug input field
        dbgString = self.gui.gui.leDebugInput.text()
        # Check dbgString is valid serial command
        bWrite, txString = self.cmdStringFormat(str(dbgString))
        # Send over serial port
        self.sCom.write(txString)
        # Only read serial port if read command sent
        if bWrite is True:
            self.gui.gui.leDebugOutput.setText("Write command sent.")
        else:
            # Read reply
            rxString = self.readSerialInterface()
            if rxString is None:
                print "debugSend() received None"
                self.gui.gui.leDebugOutput.setText("debugSend() received nothing!")
                return None
            self.gui.gui.leDebugOutput.setText(str(rxString))

    def lvButtonAction(self):
        """ Execute each time lvButton is pressed """
        # If bLvEnabled True (Green), make False and turn associated LED red
        if self.bLvEnabled is True:     # lv is enabled, now Disabling...
            self.bLvEnabled = False
            self.gui.gui.lvButton.setText("enable LV")
            self.bLvGreen = False
            self.gui.gui.frmLowVoltageStatus.setStyleSheet(QtCore.QString.fromUtf8("\nbackground-color: rgb(255, 0, 0);"))
            # Disable biasButton while lv disabled
            self.gui.gui.biasButton.setEnabled(False)
        else:
            self.bLvEnabled = True      # lv is disabled, now Enabling...
            self.gui.gui.lvButton.setText("disable LV")
            self.bLvGreen = True
            self.gui.gui.frmLowVoltageStatus.setStyleSheet(QtCore.QString.fromUtf8("\nbackground-color: rgb(0, 255, 0);"))
            # Enable biasButton only after lv successfully enabled
            self.gui.gui.biasButton.setEnabled(True)

    def biasButtonAction(self):
        """ Execute each time biasButton is pressed """
        # If bBiasEnabled True, make False and turn associated LED red        
        if self.bBiasEnabled is True:   # bias is enabled, now Disabling...
            self.bBiasEnabled = False
            self.gui.gui.biasButton.setText("enable Bias")
            self.bBiasGreen = False
            self.gui.gui.frmBiasStatus.setStyleSheet(QtCore.QString.fromUtf8("\nbackground-color: rgb(255, 0, 0);"))
            # Disable Polling checkbox while bias is disabled
            self.gui.gui.cbPollingBox.setEnabled(False)
            # Disable lvButton & biasLevel until bias disabled again (prevent disabling lv/changing biasLevel while bias enabled)
            self.gui.gui.lvButton.setEnabled(True)
            self.gui.gui.leBiasLevel.setEnabled(True)
        else:
            self.bBiasEnabled = True    # bias is disabled, now Enabling...
            self.gui.gui.biasButton.setText("disable Bias")
            self.bBiasGreen = True
            self.gui.gui.frmBiasStatus.setStyleSheet(QtCore.QString.fromUtf8("\nbackground-color: rgb(0, 255, 0);"))
            # Enable file selection only after bias successfully enabled
            self.gui.gui.selectButton.setEnabled(True)
            self.gui.gui.leSelectLogFileLocation.setEnabled(True)
            self.gui.gui.cbPollingBox.setEnabled(True)
            # Disable lvButton & biasLevel until bias disabled again (prevent disabling lv/changing biasLevel while bias enabled)
            self.gui.gui.lvButton.setEnabled(False)
            self.gui.gui.leBiasLevel.setEnabled(False)

#    def toggleVisibleGuiComponents(self, bEnable):
#        """ Hide/Display (Disable/Enable) GUI components by group """
#        # Is bBool a boolean?
#        if compareTypes(bEnable) is not 4:
#            raise WrongVariableType, "toggleVisibleGuiComponents() was not passed a boolean argument!"  
#        # Enable/Disable
#        self.gui.gui.gbMonitor.setEnabled(bEnable)   # Monitor
#        self.gui.gui.gbPower.setEnabled(bEnable)     # Power
#        self.gui.gui.gbDebug.setEnabled(bEnable)     # Debug
#        return bEnable
    
    def lwSerialPortChosen(self):
        """ Called when an item is clicked inside the lwSerialPort
        Go through list of available COM ports in self.availableComPorts while comparing lwSerialPort.currentRow()
        to find which COM port selected. Note that in some cases com ports on a PC are not in numerical order,
        i.e., there is no COM2 on my machine currently:
        [(0, 'COM1'), (2, 'COM3'), (3, 'COM4')]
        for that reason, currentLine is used, since comparing cNo against .currentRow() would never catch COM3
        if it were selected on my machine.
        """
        currentLine = 0
        # Go through each pair of (port number, port string) in list self.availableComPorts
        for cNo,cStr in self.availableComPorts:
            # Is this pair the selected com port?
            if currentLine is self.gui.gui.lwSerialPort.currentRow():
                ''' Found the selected COM port, open port cNo '''
                # Open serial port only if not already open!
                if self.sCom is False:
                    try:
                        self.sCom = serial.Serial(port=cNo, baudrate = 57600, timeout = 1)
                        # If port successfully open, enable bias level control & lvButton
                        self.gui.gui.leBiasLevel.setEnabled(True)
                        self.gui.gui.lvButton.setEnabled(True)
                    except:
                        ''' In practice, this will rarely fail unless selected port already in use '''
                        self.displayErrorMessage("Unable to open COM port: ", cNo)
                        # Stop polling data - no serial connection available
                        self.gui.gui.cbPollingBox.setChecked(False)
                        self.bPollingEnabled = False
            # Increment currentLine before next iteration
            currentLine = currentLine + 1

        
    def cmdStringFormat(self, sCmd):
        """ Checks that argument sCmd is a valid read or write command string
            Predominantly intended for debugSend
        """
        # Check sCmd doesn't contain non-decimal digit except first/final char
        # .replace(' ','') removes all whitespaces from string
        # [1:-1] omits first and last char
        # .isdigit() is True if string only digits, False for any other char
        if sCmd.replace(' ','')[1:-1].isdigit() is False:
            raise MalformedStringError, "cmdStringFormat() Found non-digit(s) apart from 1st/last char!"
        # Make sure sCmd is a String object
        sCmd = str(sCmd)
        # Theoretically, string cannot be shorter than seven characters: "w 1 2 @"
        if sCmd.__len__() < 7:
            raise MalformedStringError, "cmdStringFormat() sCmd too short!"
        # Check String starts with w, W, r or R
        if not ((sCmd[0].lower() == 'w') or (sCmd[0].lower() == 'r')):
            raise MalformedStringError, "cmdStringFormat() sCmd doesn't start with w, W, r or R!"
        # String must end with @
        if sCmd[-1] != '@':
            raise MalformedStringError, "cmdStringFormat() sCmd doesn't end with @!"
        # Make sure space after first character(w/r) and before last character (@)
        if not ((sCmd[1] == ' ') and (sCmd[-2] == ' ')):
            raise MalformedStringError, "cmdStringFormat() sCmd missing space after first/before last character!"
        # sCmd appears valid at this point, check if read or write
        if sCmd[0].lower() == 'w':
            # Found w/W, return True and sCmd
            return True, sCmd
        else:
            return False, sCmd

    def toggleDebugComponents(self, bEnable):
        """ This function will enable/disable the two debug fields and the debug button """
        # Is bEnable a boolean?
        if compareTypes(bEnable) is not 4:
            raise WrongVariableType, "toggleDebugComponents() was not passed a boolean argument!"
        # Toggle enable/disable according to bEnable
        self.gui.gui.leDebugInput.setEnabled(bEnable)
        self.gui.gui.leDebugOutput.setEnabled(bEnable)
        self.gui.gui.debugButton.setEnabled(bEnable)
        return bEnable

    def toggleSelectFileComponents(self, bEnable):
        """ toggleSelectFileComponents enables/disables selectButton &  """
        # Is bEnable a boolean?
        if compareTypes(bEnable) is not 4:
            raise WrongVariableType, "toggleSelectFileComponents() was not passed a boolean argument!"
        # Toggle enable/disable according to bEnable
        self.gui.gui.selectButton.setEnabled(bEnable)
        self.gui.gui.leSelectLogFileLocation.setEnabled(bEnable)
        return bEnable

    def displayWarningMessage(self, warningString):
        """ Constructs a string from warningString and the system info (whether available),
            and display this in the GUI """
        if compareTypes(warningString) is not 3:
            raise WrongVariableType, "displayWarningMessage() did not receive a string type argument!"
        warningMsg = str(warningString)
        if sys.exc_info()[1] is not None:
            warningMsg = warningMsg + " " + str(sys.exc_info()[1])  # Append descriptive message
        if sys.exc_info()[0] is not None:
            warningMsg = warningMsg + " " + str(sys.exc_info()[0])  # Append error type
        self.msgPrint( warningMsg )

    def displayErrorMessage(self, errorString):
        """ Constructs a string from errorString and the other argument(s) (if provided),
            displaying this in the GUI and print it to console """
        if compareTypes(errorString) is not 3:
            raise WrongVariableType, "displayErrorMessage() did not receive a string type argument!"
        errorMsg = str(errorString)
        if sys.exc_info()[1] is not None:
            errorMsg = errorMsg + " " + str(sys.exc_info()[1])  # Append descriptive message
        if sys.exc_info()[0] is not None:
            errorMsg = errorMsg + " " + str(sys.exc_info()[0])  # Append error type
        self.msgPrint( errorMsg )
        # Log error to file, but only if i2c device is initialised and Header written to file
        if (self.bInitialisation is False) and (self.bLogHeader is False):
            self.logError(str(errorMsg))
        return True
#------------------------------#

    def readSerialInterface(self):
        """ read serial port, and fail gracefully invalid or none available """
        if not self.sCom.isOpen():
            self.displayErrorMessage("readSerialInterface() Serial port closed!")
            return None
        while(self.sCom.inWaiting() is 0):
            self.displayWarningMessage("Waiting for serial data..")
            time.sleep(0.3)
        # Read serial port until \n
        try:
            rxString = self.sCom.readline()
        except:
            # Occasionally throws Handle Exception when GUI exits
            self.displayErrorMessage("readSerialInterface(), exception: ")
            print self.sCom
            return None

        if rxString.__len__() is 0:
            # No reply, wait 500 ms and retry serial interface
            time.sleep(0.5)
            # Retry
            rxString = self.sCom.readline()
            if rxString.__len__() == 0:
                print "2nd attempt, rxString: (empty)"
                self.displayErrorMessage("Serial Comm: Reply timed out!")
                return None
        # 1st or 2nd attempt successful, return data
        return rxString
        
#------------------------------#
    
    def lm92ToDegrees(self, temp):
        """ Convert lm92 13 bit format into degrees centigrade
            valid range, arduino restriction: 0c - +150c
            valid range, lm92 13 bit format: 4 - 19200         """
        lm92Temp = int(temp)
        # Valid range  4 =< temp =< 19200
        if not (4 <= lm92Temp <= 19200):
            raise OutOfRangeError, "lm92 format valid range: 4 <= n <= 19200"

        lm92Value = (lm92Temp >>3)*0.0625

        thresholdAnswer = self.compareThresholds(lm92Value, self.humidityMin, self.humidityMax, self.humidityWarn)
        if thresholdAnswer is 0:
            self.updateHumidityLed(thresholdAnswer) #Green
        elif thresholdAnswer is 1:
            self.updateHumidityLed(thresholdAnswer) #Amber
        elif thresholdAnswer is 2:
            self.updateHumidityLed(thresholdAnswer) #Red
        else:
            self.displayErrorMessage("lm92ToDegrees() error: minimum exceeded maximum!")
            return None
        return lm92Value
        
    def compareThresholds(self, val, minVal, maxVal, warn):
        """ Compare val to minimum (minVal), maximum (maxVal) and warning (warn) thresholds
            and return integer accordingly (0 = Green, 1 = Amber, 2 = Red) """
        # Check 1st argument is float and other arguments are integers only
        if ( compareTypes(val) is not 2):
            raise BadArgumentError, "compareThresholds() error: Received unexpected val argument type"
        elif compareTypes(minVal) is not 1:
            raise BadArgumentError, "compareThresholds() error: Received unexpected minVal argument type"
        elif compareTypes(maxVal) is not 1:
            raise BadArgumentError, "compareThresholds() error: Received unexpected maxVal argument type"
        elif compareTypes(warn) is not 1:
            raise BadArgumentError, "compareThresholds() error: Received unexpected warn argument type"            
        # maxVal must be greater than minVal
        if not (maxVal > minVal):
            raise OutOfRangeError, "compareThresholds: maxVal must be greater than minVal!" 
        if (val <= minVal) or (val >= maxVal):
            return 2        # "Red"
        elif (minVal <= val <= minVal+warn) or (maxVal-warn <= val <= maxVal): 
            return 1        # "Amber"
        else:
            return 0        # "Green"
    
    def updateHumidityLed(self, colour):
        """ Update Humidity Status in Gui to colour's colour
            Note: colour must be either: 0 (Green), 1 (Amber) or 2 (Red) """
        if colour is 0: #"Green"
            self.bHumidityGreen = True
            humidityStatus = "frmHumidityStatus=\nbackground-color: rgb(0, 255, 0);"
        elif colour is 1: #"Amber"
            self.bHumidityGreen = True  # Amber considered true as it's a warning but not yet out of range
            humidityStatus = "frmHumidityStatus=\nbackground-color: rgb( 255, 255, 0);"
        elif colour is 2: #"Red"
            self.bHumidityGreen = False
            humidityStatus = "frmHumidityStatus=\nbackground-color: rgb(255, 0, 0);"
        else:
            raise BadArgumentError, "updateHumidityLed argument neither 0, 1 or 2 (i.e. Green/Amber/Red)!"
            return False
        # Signal to update Gui component
        self.queue.put(humidityStatus)
        return True

    def updateAirTempLed(self, colour):
        """ Update Air Temperature Status in Gui to colour's colour
            Note: colour must be either: 0 (Green), 1 (Amber) or 2 (Red) """
        if colour is 0: #"Green":
            self.bAirTempGreen = True
            airStatus = "frmAirTempStatus=\nbackground-color: rgb(0, 255, 0);"
        elif colour is 1: #"Amber":
            self.bAirTempGreen = True  # Amber considered true as it's a warning but not yet out of range
            airStatus = "frmAirTempStatus=\nbackground-color: rgb( 255, 255, 0);"
        elif colour is 2: #"Red":
            self.bAirTempGreen = False
            airStatus = "frmAirTempStatus=\nbackground-color: rgb(255, 0, 0);"
        else:
            raise BadArgumentError, "updateAirTempLed argument neither 0, 1 or 2 (i.e. Green/Amber/Red)!"
            return False        
        # Signal to update Gui component
        self.queue.put(airStatus)
        return True

    def updateCoolantFlowLed(self, colour):
        """ Update Coolant Flow Status in Gui to colour's colour
            Note: colour must be either: 0 (Green), 1 (Amber) or 2 (Red) """
        if colour is 0: #"Green":
            self.bCoolantFlowGreen = True
            coolantFlowStatus = "frmCoolantFlowStatus=\nbackground-color: rgb(0, 255, 0);"
        elif colour is 1: #"Amber":
            self.bCoolantFlowGreen = True  # Amber considered true as it's a warning but not yet out of range
            coolantFlowStatus = "frmCoolantFlowStatus=\nbackground-color: rgb( 255, 255, 0);"
        elif colour is 2: #"Red":
            self.bCoolantFlowGreen = False
            coolantFlowStatus = "frmCoolantFlowStatus=\nbackground-color: rgb(255, 0, 0);"
        else:
            raise BadArgumentError, "updateCoolantFlowLed argument neither 0, 1 or 2 (i.e. Green/Amber/Red)!"
            return False
        # Signal to gui to update LED
        self.queue.put(coolantFlowStatus)
        return True
    
    def updateCoolantTempLed(self, colour):
        """ Update Coolant Temperature Status in Gui to colour's colour
            Note: colour must be either: 0 (Green), 1 (Amber) or 2 (Red) """
        if colour is 0: #"Green":
            self.bCoolantTempGreen = True
            coolantTempStatus = "frmCoolantTempStatus=\nbackground-color: rgb(0, 255, 0);"
        elif colour is 1: #"Amber":
            self.bCoolantTempGreen = True  # Amber considered true as it's a warning but not yet out of range
            coolantTempStatus = "frmCoolantTempStatus=\nbackground-color: rgb( 255, 255, 0);"
        elif colour is 2: #"Red":
            self.bCoolantTempGreen = False
            coolantTempStatus = "frmCoolantTempStatus=\nbackground-color: rgb(255, 0, 0);"
        else:
            raise BadArgumentError, "updateCoolantTempLed argument neither 0, 1 or 2 (i.e. Green/Amber/Red)!"
            return False
        # Signal to Gui to update LED
        self.queue.put(coolantTempStatus)
        return True

    def degreesToLm92(self, temp):
        """ Convert integer or float degrees to 13 bit temperature value """
        if compareTypes(temp) is not 1 and compareTypes(temp) is not 2:
            raise BadArgumentError, "degreesToLm92() argument not float or integer!"
        tempTest = float(temp)
        # Valid range ?
        if not (0 <= tempTest <= 150):
            raise OutOfRangeError, "lm92 temperature valid range: 0 <= n <= 150"

        # Store temp's mantissa and fraction as separate integers
        intMantissa= int(temp)
        # Binary << 1, is equivalent to Decimal * 2. Hence Dec * 16 (2^4) = Bin << 4
        intFraction = int( (temp - intMantissa)*16 )
        # To convert temp into lm92 format, left shift 7 times
        intMantissa = intMantissa << 7
        intFraction = intFraction << 3          # Only 3 times, already left shifted 4 times
        intTotal =intFraction + intMantissa
        bLow = intTotal & 0xff                  # Extract low 8 bits of temperature
        bHigh = (intTotal >> 8) & 0xff          # Extract high 8 bits of temperature
        lm92String = (str(bHigh) + " " + str(bLow))
        return lm92String       
         
    def tmpToDegrees(self, temp=0):
        """ Convert tmp temperature format into degrees centigrade 
            tmp275 range: -55c to +127c
            Arduino range: 0c to +127c
            tmp275 format: 8 <= n <= 32512
        """
        # Empty string received?
        if temp is None:
            return temp
        temp = int(temp)
        # Valid range?
        if not(8 <= temp <= 32512):
            raise OutOfRangeError, "tmp275 format valid range: 8 <= temp <= 32,512"
        
        # temp is valid, convert into degrees centigrade
        temp = temp >> 4;           # 4 LSB bits unused
        temp = float(temp * 0.0625) # 1 LSB = 0.0625C
        
        thresholdAnswer = self.compareThresholds(temp, self.humidityMin, self.humidityMax, self.humidityWarn)
        if thresholdAnswer is 0:
            self.updateAirTempLed(thresholdAnswer) #Green
        elif thresholdAnswer is 1:
            self.updateAirTempLed(thresholdAnswer) #Amber
        elif thresholdAnswer is 2:
            self.updateAirTempLed(thresholdAnswer) #Red
        else:
            self.displayErrorMessage("tmpToDegrees() error: minimum exceeded maximum!")
            return None
        return temp 

    def readtmp(self):
#        sCmd = "r 79 2 @"
#        bWr, txtString = self.cmdStringFormat(sCmd)
#        if bWr is True:
#            print "Write command"
#        else:
#            print "Read command"
        self.sCom.write("r 79 2 @")
        rxString = self.readSerialInterface()
        if rxString is None:
            self.displayErrorMessage("readtmp() No serial!")
            return None
        # Convert tmp275 format into degrees centigrade
        rxString = self.tmpToDegrees(rxString)
        rndString = round3Decimals(rxString)
        msg = "leAirtmp_mon="
        msg = msg + str(rndString)
        self.queue.put(msg)
        return rxString

    def readvolt(self):
        self.sCom.write("r 35 2 @")
        rxString = self.readSerialInterface()
        if rxString is None:
            self.displayErrorMessage("readvolt() read None!")
            return None
        print "Received Ad7998 value: ", rxString

    def writelm92(self, sReg, sVal=None):
        """ Write to lm92 selecting register and optionally
            its new value. E.g. Select high temp register:
            writelm92(5)
            Change Critical temp register to 81C:
            writelm92(3, 81)
            Note!   Valid register (sReg) range: 0-7
            Note2!  Current (untested) function only supports
                    positive temperatures: 0-150C
        """
        if sReg is None:
            raise ArgumentTypeNoneError, "writelm92() sReg not specified"
        # Suitable sReg?
        if not (0 <= int(sReg) <= 7):
            raise OutOfRangeError, "writelm92() sReg argument out of range"
        # Check sVal suitable, provided it's not None
        if sVal is not None:
            if not (0 <= sVal <= 150):
                raise OutOfRangeError, "writelm92() sVal argument out of range"
        # Was sVal specified?
        if sVal is not None:
            # Change sVal into lm92's 13 bit format:
            sVal =  self.degreesToLm92(sVal)
            # Construct lm92 write command specifying register and value
            wrString = "w 75 " + str(sReg) + " " + str(sVal) + " @"
        else:
            # Construct lm92 write command with only register
            wrString = "w 75 " + str(sReg) + " @"            
        self.sCom.write(wrString)        

    def readlm92(self):
        """ Read from lm92 device """
        self.sCom.write("r 75 2 @")
        rxString = self.readSerialInterface()
        if rxString is None:
            self.displayErrorMessage("readlm92() read None!")
            return None
        if int(rxString) < 0:
            self.displayErrorMessage("readlm92() found negative value: ", rxString)
            return None
        # Convert into degrees centigrade
        rxString = self.lm92ToDegrees(rxString)
        rxString = round3Decimals(rxString)
        msg = "leHum_mon="
        msg = msg + str(str(rxString))
        # Send to excaliburPowerGuiMain, who'll update GUI
        self.queue.put(msg)
        return rxString
    
    def readpca9538(self):
        """ Read from pca9538 device """
        self.sCom.write("r 113 1 @")
        rxString = self.readSerialInterface()
        if rxString is None:
            self.displayErrorMessage("readpca9538() read None!")
            return None
        rxVal = int(rxString)
#        print "pca9538: ", rxVal
        # Pin 0
        if rxVal & 1 is 1:
            # Humidity's High
            if self.bHumidityGreen is False:
                # Only change to Green if previously Red
                self.gui.gui.frmHumidityStatus.setStyleSheet(QtCore.QString.fromUtf8("\nbackground-color: rgb(0, 255,  0);"))
                self.bHumidityGreen = True
        else:
            # Ensure Humidity's Red if previously Green
            if self.bHumidityGreen is True:
                self.gui.gui.frmHumidityStatus.setStyleSheet(QtCore.QString.fromUtf8("\nbackground-color: rgb(255, 0, 0);"))
                self.bHumidityGreen = False                
        # Pin 1
        if rxVal & 2 is 2:
            # Coolant Flow's gone
            if self.bCoolantFlowGreen is False:
                # Only change to Green if previously Red
                self.queue.put("frmAirTempStatus=\nbackground-color: rgb(0, 255,  0);")
                self.bCoolantFlowGreen = True
        else:
            # Ensure Coolant Flow's Red if previously Green
            if self.bCoolantFlowGreen is True:
                self.queue.put("frmAirTempStatus=\nbackground-color: rgb(255, 0, 0);")
                self.bCoolantFlowGreen = False
        # Pin 2
        if rxVal & 4 is 4:
            # Coolant Temp's gone low
            if self.bCoolantTempGreen is False:
                # Only change to Green if previously Red
                self.gui.gui.frmCoolantFlowStatus.setStyleSheet(QtCore.QString.fromUtf8("\nbackground-color: rgb(0, 255,  0);"))
                self.bCoolantTempGreen = True
        else:
            # Ensure Coolant Temp's Red if previously Green
            if self.bCoolantTempGreen is True:
                self.gui.gui.frmCoolantFlowStatus.setStyleSheet(QtCore.QString.fromUtf8("\nbackground-color: rgb(255, 0, 0);"))
                self.bCoolantTempGreen = False
        # Pin 3
        if rxVal & 8 is 8:
            # Air Temp's gone low
            if self.bAirTempGreen is False:
                # Only change to Green if previously Red
                self.gui.gui.frmCoolantTempStatus.setStyleSheet(QtCore.QString.fromUtf8("\nbackground-color: rgb(0, 255,  0);"))
                self.bAirTempGreen = True
        else:
            # Ensure Air Temp's Red if previously Green
            if self.bAirTempGreen is True:
                self.gui.gui.frmCoolantTempStatus.setStyleSheet(QtCore.QString.fromUtf8("\nbackground-color: rgb(255, 0, 0);"))
                self.bAirTempGreen = False

    def initialiseCommunication(self):
        # pca9538
        self.sCom.write("w 113 0 @")    # Configure I2C expander, access register 0 (I/O pins)
        # lm92
        self.writelm92(0)
#        self.sCom.write("w 75 0 @")     # Select temperature register in lm92
        # tml275
        self.sCom.write("w 79 1 96 @")  # Initialise tmp275 device
        self.sCom.write("w 79 0 @")     # Select temperature register
        # Configure ad7998 device
        self.sCom.write("w 35 2 0 16 @")    # Config Reg (2): Enable Channel 1 (0 16)
        self.sCom.write("w 35 112 @")       # Set command bits in reg (mode 2 - command mode selected)
        self.sCom.write("w 35 3 1 @")       # Set Cycle Timer Register
        self.sCom.write("w 35 0 @")         # Point at Conversion Result Register

#------------------------------##------------------------------#

    def readAd7998(self, address = 0):
        """ Read ad7998 device at address and determine
            which adc channel responded """
        # Check argument is integer and specified
        if compareTypes(address) is not 1 or address is 0:
            raise ArgumentTypeNoneError, "readAd7998(): address argument not specified or invalid"
        sCmd = "r " + str(address) + " 2 @"
        try:
            self.sCom.write(sCmd)
        except:
            self.displayErrorMessage("readAd7998(), Serial exception: ")
        rxString = self.readSerialInterface()
        adcChannel = 0
        # No serial data?
        if rxString is None:
            return -1, -1
        else:
            rxInt = int(rxString)       # Convert ADC value to integer
            adcChannel = rxInt >> 12    # Bit 13-16 determine ADC channel number
            # Scale adc's value to 0-4095 range 
            rxInt = rxInt - (adcChannel*4096)
            # Each adc has its own range 
            # abc0: 0-4095, adc1: 4096-8191, adc2: 8192-12287
            return adcChannel, rxInt

    def scale5V(self, adcValue):
        """ Scale ad7998's range of ADC count: 0-4095 to 0-5Volts """
        # Ensure adcValue is integer
        adcValue=int(adcValue)
        # Check adcValue 0-4095
        if not (0 <= adcValue <= 4095):
            raise OutOfRangeError, "scale5V() adcValue outside 0-4095 range!"
        return (adcValue / 819.0)

    def scale1_8V(self, adcValue):
        """ Scale ad7998's range of ADC count: 0-4095 to 0-1.8Volts """
        # Ensure adcValue is integer
        adcValue=int(adcValue)
        # Check adcValue 0-4095
        if not (0 <= adcValue <= 4095):
            raise OutOfRangeError, "scale1_8V() adcValue outside 0-4095 range!"
        return (adcValue / 2275.0)
    
    def scale3_3V(self, adcValue):
        """ Scale ad7998's range of ADC count: 0-4095 to 0-3.3Volt """
        # Ensure adcValue is integer
        adcValue=int(adcValue)
        # Check adcValue 0-4095
        if not (0 <= adcValue <= 4095):
            raise OutOfRangeError, "scale3_3V() adcValue outside 0-4095 range!"
        return (adcValue *(11 / 13650.0))        
    
    def readAd7998_Unit14(self, ch8to5, ch4to1):
        """ Select ad7998's channel(s) according to arguments,
            select conversion register and call readAd7998()
            to read ADC value of selected channel
            Only bits D11-D4** determine channel selection, therefore
            valid ranges: 0 <= ch8to5 <= 8 
                         0,16 <= ch4to1 <= 128 (i.e. can be 0, or 16-128)
                         **(1=D0, 2=D1, 4=D2, 8=D3;  D0-D3 =  N/A) 
        """
        if compareTypes(ch8to5) is not 1 or compareTypes(ch4to1) is not 1:
            raise BadArgumentError, "readAd7998_Unit14() one or more arguments not integer"
        if not (0 <= ch8to5 <= 8):
            raise OutOfRangeError, "readAd7998_Unit14() ch8to5 argument out of range"
        if not (16 <= ch4to1 <= 128) and not (ch4to1 is 0):
            raise OutOfRangeError, "readAd7998_Unit14() ch4to1 argument out of range"
        # Unit testing only: return True if argument testing successful
        if self.bTest is True:
            return True
        sCmd = "w 35 2 " + str(ch8to5) + " " + str(ch4to1) + " @"
        try:
            self.sCom.write(sCmd)
            # Select conversion register
            self.sCom.write("w 35 0 @")
            # Read enabled channel at address 35
            adcChannel, rxInt = self.readAd7998(35)
        except:
            self.displayErrorMessage("readAd7998_Unit14(), Serial exception: ")
        # Local functions handling ADC dictionary lookup
        def zero():
            try:    self.queue.put("le5VAV=%s" % str( round2Decimals( self.scale5V(rxInt)) ))   # Unit 14, pin 7
            except: self.displayErrorMessage("U14 adc0, Error updating GUI: ")
        def one():
            try:    self.queue.put("le5VBV=%s" % str( round2Decimals(self.scale5V(rxInt)) ))   # Unit 14, pin 14
            except: self.displayErrorMessage("U14 adc1, Error updating GUI: ")
        def two():
            try:    self.queue.put("le5F0I=%s" % str( round2Decimals(self.scale5V(rxInt)) ))   # Unit 14, pin 8
            except: self.displayErrorMessage("U14 adc2, Error updating GUI: ")
        def three():
            try:    self.queue.put("le5F1I=%s" % str( round2Decimals(self.scale5V(rxInt)) ))   # Unit 14, pin 13
            except: self.displayErrorMessage("U14 adc3, Error updating GUI: ")
        def four():
            try:    self.queue.put("le5F2I=%s" % str( round2Decimals(self.scale5V(rxInt)) ))   # Unit 14, pin 9
            except: self.displayErrorMessage("U14 adc4, Error updating GUI: ")
        def five():
            try:    self.queue.put("le5F3I=%s" % str( round2Decimals(self.scale5V(rxInt)) ))   # Unit 14, pin 12
            except: self.displayErrorMessage("U14 adc5, Error updating GUI: ")
        def six():
            try:    self.queue.put("le5F4I=%s" % str( round2Decimals(self.scale5V(rxInt)) ))   # Unit 14, pin 10
            except: self.displayErrorMessage("U14 adc6, Error updating GUI: ")
        def seven():
            try:    self.queue.put("le5F5I=%s" % str( round2Decimals(self.scale5V(rxInt)) ))   # Unit 14, pin 11
            except: self.displayErrorMessage("U14 adc7, Error updating GUI: ")
        # Create dictionary lookup for channel number
        whichChannel = {0 : zero, 1 : one, 2 : two, 3 : three, 4 : four,
                        5 : five, 6 : six, 7 : seven,}
        # Lookup ADC channel
        try:
            whichChannel[adcChannel]()
        except:
            self.displayWarningMessage("Ad7998_U14 Received unrecognisable ADC data!")
            print "U14 adcChannel: ", adcChannel, " rxInt: ", rxInt            

    def readAd7998_Unit15(self, ch8to5, ch4to1):
        """ Select ad7998's channel(s) according to arguments,
            select conversion register and call readAd7998()
            to read ADC value of selected channel
            Only bits D11-D4** determine channel selection, therefore
            valid ranges: 0 <= ch8to5 <= 8 
                         0,16 <= ch4to1 <= 128 (i.e. can be 0, or 16-128)
                         **(1=D0, 2=D1, 4=D2, 8=D3;  D0-D3 =  N/A) 
        """
        if compareTypes(ch8to5) is not 1 or compareTypes(ch4to1) is not 1:
            raise BadArgumentError, "readAd7998_Unit15() one or more arguments not integer"
        if not (0 <= ch8to5 <= 8):
            raise OutOfRangeError, "readAd7998_Unit15() ch8to5 argument out of range"
        if not (16 <= ch4to1 <= 128) and not (ch4to1 is 0):
            raise OutOfRangeError, "readAd7998_Unit15() ch4to1 argument out of range"
        # Unit testing only: return True if argument testing successful
        if self.bTest is True:
            return True
        i2cAddress = 0
        sCmd = "w " + str(i2cAddress) + " 2 " + str(ch8to5) + " " + str(ch4to1) + " @"
        try:
            self.sCom.write(sCmd)
            # Select conversion register
            sCmd = "w " + str(i2cAddress) + " 0 @"
#            self.sCom.write("w 35 0 @")
            self.sCom.write(sCmd)
            # Read enabled channel at address ..
            adcChannel, rxInt = self.readAd7998(i2cAddress) 
        except:
            self.displayErrorMessage("readAd7998_Unit15(), Serial exception: ")
        # Local functions handling ADC dictionary lookup
        def zero():
            try:    self.queue.put("le48VV=%s" % str( rxInt ))      # U15, pin 7
            except: self.displayErrorMessage("U15 adc0, Error updating GUI: ")
        def one():
            try:    self.queue.put("le48VA=%s" % str( self.scale5V(rxInt) ))        # U15, pin 14
            except: self.displayErrorMessage("U15 adc1, Error updating GUI: ")
        def two():
            try:    self.queue.put("le5SUPERVV=%s" % str( self.scale5V(rxInt) ))        # U15, pin 8
            except: self.displayErrorMessage("U15 adc2, Error updating GUI: ")
        def three():
            try:    self.queue.put("le5SUPERVA=%s" % str( self.scale5V(rxInt) ))        # U15, pin 13
            except: self.displayErrorMessage("U15 adc3, Error updating GUI: ")
        def four():
            try:    self.queue.put("leHum_mon=%s" % str( self.scale5V(rxInt) ))        # U15, pin 9
            except: self.displayErrorMessage("U15 adc4, Error updating GUI: ")
        def five():
            try:    self.queue.put("leAirtmp_mon=%s" % str( self.scale5V(rxInt) ))        # U15, pin 12 
            except: self.displayErrorMessage("U15 adc5, Error updating GUI: ")
        def six():
            try:    self.queue.put("leCoolant_temp_mon=%s" % str( self.scale5V(rxInt) ))        # U15, pin 10
            except: self.displayErrorMessage("U15 adc6, Error updating GUI: ")
        def seven():
            try:    self.queue.put("leCoolant_flow_mon=%s" % str( self.scale5V(rxInt) ))        # U15, pin 11
            except: self.displayErrorMessage("U15 adc7, Error updating GUI: ")
        # Create dictionary lookup for channel number
        whichChannel = {0 : zero, 1 : one, 2 : two, 3 : three, 4 : four,
                        5 : five, 6 : six, 7 : seven,}
        # Lookup ADC channel
        try:
            whichChannel[adcChannel]()
        except:
            self.displayWarningMessage("Ad7998_U15 Received unrecognisable ADC data!")
            print "U15 adcChannel: ", adcChannel, " rxInt: ", rxInt            

    def readAd7998_Unit16(self, ch8to5, ch4to1):
        """ Select ad7998's channel(s) according to arguments,
            select conversion register and call readAd7998()
            to read ADC value of selected channel
            Only bits D11-D4** determine channel selection, therefore
            valid ranges: 0 <= ch8to5 <= 8 
                         0,16 <= ch4to1 <= 128 (i.e. can be 0, or 16-128)
                         **(1=D0, 2=D1, 4=D2, 8=D3;  D0-D3 =  N/A) 
        """        
        if compareTypes(ch8to5) is not 1 or compareTypes(ch4to1) is not 1:
            raise BadArgumentError, "readAd7998_Unit16() one or more arguments not integer"
        if not (0 <= ch8to5 <= 8):
            raise OutOfRangeError, "readAd7998_Unit16() ch8to5 argument out of range"
        if not (16 <= ch4to1 <= 128) and not (ch4to1 is 0):
            raise OutOfRangeError, "readAd7998_Unit16() ch4to1 argument out of range"
        # Unit testing only: return True if argument testing successful
        if self.bTest is True:
            return True
        i2cAddress = 0        
        sCmd = "w " + str(i2cAddress) + " 2 " + str(ch8to5) + " " + str(ch4to1) + " @"
        try:
            self.sCom.write(sCmd)
            # Select conversion register
            sCmd = "w " + str(i2cAddress) + " 0 @"
#            self.sCom.write("w 35 0 @")
            self.sCom.write(sCmd)
            # Read enabled channel at address ..
            adcChannel, rxInt = self.readAd7998(i2cAddress) 
        except:
            self.displayErrorMessage("readAd7998_Unit16(), Serial exception: ")
        # Local functions handling ADC dictionary lookup
        def zero():
            try:    self.queue.put("le33VA=%s" % str( rxInt ))      # U16, pin 7
            except: self.displayErrorMessage("U16 adc0, Error updating GUI: ")
        def one():
            try:    self.queue.put("le18VAA=%s" % str( self.scale5V(rxInt) ))        # U16, pin 14
            except: self.displayErrorMessage("U16 adc1, Error updating GUI: ")
        def two():
            try:    self.queue.put("le200VA=%s" % str( self.scale5V(rxInt) ))        # U16, pin 8
            except: self.displayErrorMessage("U16 adc2, Error updating GUI: ")
        def three():
            try:    self.queue.put("le33VV=%s" % str( self.scale5V(rxInt) ))        # U16, pin 13
            except: self.displayErrorMessage("U16 adc3, Error updating GUI: ")
        def four():
            try:    self.queue.put("le18VVA=%s" % str( self.scale5V(rxInt) ))        # U16, pin 9
            except: self.displayErrorMessage("U16 adc4, Error updating GUI: ")
        def five():
            try:    self.queue.put("le200VV=%s" % str( self.scale5V(rxInt) ))        # U16, pin 12 
            except: self.displayErrorMessage("U16 adc5, Error updating GUI: ")
        def six():
            try:    self.queue.put("le18VAB=%s" % str( self.scale5V(rxInt) ))        # U16, pin 10
            except: self.displayErrorMessage("U16 adc6, Error updating GUI: ")
        def seven():
            try:    self.queue.put("le18VVB=%s" % str( self.scale5V(rxInt) ))        # U16, pin 11
            except: self.displayErrorMessage("U16 adc7, Error updating GUI: ")
        # Create dictionary lookup for channel number
        whichChannel = {0 : zero, 1 : one, 2 : two, 3 : three, 4 : four,
                        5 : five, 6 : six, 7 : seven,}
        # Lookup ADC channel
        try:
            whichChannel[adcChannel]()
        except:
            self.displayWarningMessage("Ad7998_U16 Received unrecognisable ADC data!")
            print "U16 adcChannel: ", adcChannel, " rxInt: ", rxInt            


    def doEventHandler(self):
        """ Event handling function, called for each poll
            (when in polling mode)
        """
        try:
            self.readlm92()          # Read lm92's current temperature
            self.readtmp()           # Read tmp275's current temperature
#            self.readpca9538()       # Read pca9538's current value

            self.readAd7998_Unit14(0, 16)  # Read ad7998 Ch 1
            self.readAd7998_Unit14(0, 32)  # Read ad7998 Ch 2
            self.readAd7998_Unit14(0, 64)  # Read ad7998 Ch 3
            self.readAd7998_Unit14(0, 128) # Read ad7998 Ch 4

            self.readAd7998_Unit14(1, 0)  # Read ad7998 Ch 5
            self.readAd7998_Unit14(2, 0)  # Read ad7998 Ch 6
            self.readAd7998_Unit14(4, 0)  # Read ad7998 Ch 7
            self.readAd7998_Unit14(8, 0)  # Read ad7998 Ch 8
        except:
            self.displayErrorMessage("")
        # Gui now completely populated, allow logging to proceed
        self.bInitialisation = False

#------------------------------#

# Code in scanSerialPorts() borrowed from example at: 
# http://pyserial.sourceforge.net/examples.html#finding-serial-ports
def scanSerialPorts():
    """scan for available ports. return a list of tuples (num, name)"""
    available = []
    for i in range(256):
        try:
            s = serial.Serial(i)
            available.append( (i, s.portstr))
            s.close()   # explicit close 'cause of delayed GC in java
        except serial.SerialException:
            pass
    return available

#------------------------------#

def compareTypes(var):
    """ Compare variable var's type, return integer according to:
        0 = NoneType
        1 = integer (type)
        2 = float
        3 = string
        4 = boolean """
    if type(var) is type(None):
        return 0
    if type(var) is type(2):
        return 1
    if type(var) is type(1.1):
        return 2
    if type(var) is type("h"):
        return 3
    if type(var) is type(True):
        return 4
    return -1       # Wtf? = Only possible if passing a function's object

def round2Decimals(floatVar):
    """ Round float floatVar to 2 decimal points and return as string """
    if compareTypes(floatVar) is not 2:
        raise WrongVariableType, "round2Decimals() didn't receive string argument!"
    return str("%.2f" % floatVar)

def round3Decimals(floatVar):
    """ Round float floatVar to 3 decimal points and return as string """
    if compareTypes(floatVar) is not 2:
        raise WrongVariableType, "round3Decimals() didn't receive string argument!"
    return str("%.3f" % floatVar)


if __name__ == "__main__":
    # Execute actual program
    app = QtGui.QApplication(sys.argv)
    client = ExcaliburPowerGui(app)
    sys.exit(app.exec_())
