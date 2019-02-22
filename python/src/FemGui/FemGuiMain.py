import os, sys
from FemGuiMainWindow import *
from FemClient.FemClient import *
from FemApi.FemConfig import *

class FemGuiMain:
    
    def __init__(self, app):
        
        # Initialise default state
        self.femConnected = False
        self.theFem = None
        self.femConnectionTimeout = 5.0
        self.app = app
        self.femErrString = ""
        self.defaultAddr = '192.168.1.10'
        self.defaultPort = 6969
        self.fem_config = None
        
        # Create the main window GUI and show it
        self.mainWindow= FemGuiMainWindow(self)
        self.mainWindow.show()
        
    def femConnect(self, addressStr, portStr):
        
        try:
            self.theFem = FemClient((addressStr, int(portStr)), timeout=self.femConnectionTimeout)
        except FemClientError as e:
            self.femConnected = False
            self.femErrString = "ERROR: connection failed: " + e.msg
        else:    
            self.femConnected = True
            self.femErrString = ""
     
    def femDisconnect(self):
        
        if self.theFem != None:
            self.theFem.close()
            self.theFem = None
            self.femConnected = False

    def femConfigGet(self):
    
        if self.theFem != None:
            self.fem_config = self.theFem.configRead()
            
    def femConfigUpdate(self, net_mac, net_ip, net_mask, 
                        net_gw, temp_high, temp_crit, 
                        sw_major, sw_minor, fw_major, fw_minor,
                        hw_major, hw_minor, board_id, board_type):
        
        theConfig = FemConfig(net_mac, net_ip, net_mask, 
                        net_gw, temp_high, temp_crit, 
                        sw_major, sw_minor, fw_major, fw_minor,
                        hw_major, hw_minor, board_id, board_type)
        
        self.theFem.configWrite(theConfig)
         
def main():
        
    app = QtGui.QApplication(sys.argv)  
    femGui = FemGuiMain(app)
    
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()
    