from PyQt4 import QtCore, QtGui
from FemGuiMainWindow_ui import Ui_MainWindow
from utilities import *

class FemGuiMainWindow(QtGui.QMainWindow):
    
    def __init__(self, guiMain):
        
        # Create main window UI
        
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.guiMain = guiMain
        
        # Initialise default fields based on guiMain object
        self.ui.connectAddr.setText(self.guiMain.defaultAddr)
        self.ui.connectPort.setText(str(self.guiMain.defaultPort))
        
        # Create a status bar with a progress bar
        self.createStatusBar("Not connected")
       
        # Connect signals and slots
        QtCore.QObject.connect(self.ui.connectButton, QtCore.SIGNAL("clicked()"), self.femConnectToggle)
        QtCore.QObject.connect(self.ui.configUpdateButton, QtCore.SIGNAL("clicked()"), self.updateConfig)
        self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'), self.quitApplication)
        
    def createStatusBar(self, defaultMessage):
        sb = QtGui.QStatusBar()
        sb.setFixedHeight(18)
        self.setStatusBar(sb)
        self.statusBar().showMessage(self.tr(defaultMessage))
        self.progressBar = QtGui.QProgressBar(self.statusBar())
        self.statusBar().addPermanentWidget(self.progressBar)
        self.progressBar.hide()
                            
    def femConnectToggle(self):
        
        if not self.guiMain.femConnected:

            # Extract address and port from GUI fields and validate
            femAddress = str(self.ui.connectAddr.text())
            femPort = str(self.ui.connectPort.text())
            if not validIpAddress(femAddress) or not validPort(femPort):
                ret = QtGui.QMessageBox.critical(self, "Connection error", "Please enter a valid address and port")
                return
            
            self.ui.connectButton.setEnabled(False)
            self.msgPrint("Connecting to FEM at address " + femAddress + " port " + femPort + ' ... ', term='')
            self.statusBar().showMessage(self.tr("Connecting to FEM..."))
            self.progressBar.show()
            self.progressBar.setRange(0,0)  
            self.connectThread = FemConnectThread(self.guiMain, femAddress, femPort)
            self.connectThread.connectDone.connect(self.connectDone)
            self.connectThread.start()      
        
        else:
            self.guiMain.femDisconnect()
            self.msgPrint("FEM disconnected")
            self.statusBar().showMessage(self.tr("Not connected"))
            self.ui.connectButton.setText("Connect")
            self.ui.configGroupBox.setEnabled(False)
    
    def connectDone(self):
        
        self.progressBar.hide()
        self.ui.connectButton.setEnabled(True)
        # Toggle button text according to state
        if self.guiMain.femConnected:
            self.msgPrint("OK")
            self.statusBar().showMessage(self.tr("Connected to FEM"))
            self.ui.connectButton.setText("Disconnect")
            self.showConfig()
            self.ui.configGroupBox.setEnabled(True)
        else:
            self.statusBar().showMessage(self.tr("Not connected"))
            self.msgPrint(self.guiMain.femErrString)
            self.ui.connectButton.setText("Connect")
            self.ui.configGroupBox.setEnabled(False)
                            
    def msgPrint(self, msg, term='\n'):
        
        self.ui.messageBox.insertPlainText(str(msg) + term)
        self.ui.messageBox.repaint()
        self.guiMain.app.processEvents()
        
    def showConfig(self):
        
        self.ui.magicNumber.setText('0x%X' % self.guiMain.fem_config.magicWord)
        self.ui.checksum.setText('0x%X' % self.guiMain.fem_config.checksum)
        self.ui.macAddress.setText(self.guiMain.fem_config.net_mac_str())
        self.ui.ipAddress.setText(self.guiMain.fem_config.net_ip_addr_str())
        self.ui.netMask.setText(self.guiMain.fem_config.net_ip_mask_str())
        self.ui.gateway.setText(self.guiMain.fem_config.net_ip_gw_str())
        self.ui.highTempThreshold.setText(str(self.guiMain.fem_config.temp_high))
        self.ui.critTempTreshold.setText(str(self.guiMain.fem_config.temp_crit))
        self.ui.boardId.setText(str(self.guiMain.fem_config.board_id))
        self.ui.boardType.setText(str(self.guiMain.fem_config.board_type))
        self.ui.hwVersionMajor.setText(str(self.guiMain.fem_config.hw_major_version))
        self.ui.hwVersionMinor.setText(str(self.guiMain.fem_config.hw_minor_version))
        self.ui.fwVersionMajor.setText(str(self.guiMain.fem_config.fw_major_version))
        self.ui.fwVersionMinor.setText(str(self.guiMain.fem_config.fw_minor_version))
        self.ui.swVersionMajor.setText(str(self.guiMain.fem_config.sw_major_version))
        self.ui.swVersionMinor.setText(str(self.guiMain.fem_config.sw_minor_version))
        
    def updateConfig(self):
        
        self.msgPrint("Going to update FEM EEPROM configuration")

        net_mac_str  = str(self.ui.macAddress.text()).split(':')
        net_mac      = [int(octet, 16) for octet in net_mac_str]
        net_ip_str   = str(self.ui.ipAddress.text()).split('.')
        net_ip       = [int(octet) for octet in net_ip_str]
        net_mask_str = str(self.ui.netMask.text()).split('.')
        net_mask     = [int(octet) for octet in net_mask_str]
        net_gw_str   = str(self.ui.gateway.text()).split('.')
        net_gw       = [int(octet) for octet in net_gw_str]
        temp_high    = int(self.ui.highTempThreshold.text())
        temp_crit    = int(self.ui.critTempTreshold.text())
        sw_major     = int(self.ui.swVersionMajor.text())
        sw_minor     = int(self.ui.swVersionMinor.text())
        fw_major     = int(self.ui.fwVersionMajor.text())
        fw_minor     = int(self.ui.fwVersionMinor.text())
        hw_major     = int(self.ui.hwVersionMajor.text())
        hw_minor     = int(self.ui.hwVersionMinor.text())
        board_id     = int(self.ui.boardId.text())
        board_type   = int(self.ui.boardType.text())
        
        self.guiMain.femConfigUpdate(net_mac, net_ip, net_mask, 
                        net_gw, temp_high, temp_crit, 
                        sw_major, sw_minor, fw_major, fw_minor,
                        hw_major, hw_minor, board_id, board_type)
        
        self.msgPrint("Reading configuration back")
        self.guiMain.femConfigGet()
        self.showConfig()
        
    def quitApplication(self):
        
        if self.guiMain.femConnected:
            self.guiMain.femDisconnect()
            
        self.guiMain.app.quit()

    def closeEvent(self, theCloseEvent):
        
        if self.guiMain.femConnected:
            self.guiMain.femDisconnect()
            
        theCloseEvent.accept()
        
class FemConnectThread(QtCore.QThread):

    connectDone = QtCore.pyqtSignal(bool)
 
    def __init__(self, guiMain, femAddress, femPort):
        QtCore.QThread.__init__(self)
        self.guiMain = guiMain
        self.femAddress = femAddress
        self.femPort = femPort
        
    def run(self):
        
        self.guiMain.femConnect(self.femAddress, self.femPort)
        self.guiMain.femConfigGet()
        self.connectDone.emit(True)
        