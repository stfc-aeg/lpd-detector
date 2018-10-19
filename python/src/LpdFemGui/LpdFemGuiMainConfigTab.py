'''
Created on Apr 19, 2013

@author: tcn45
'''
from PyQt4 import QtCore, QtGui
from LpdFemGuiMainWindow_ui import Ui_MainWindow
from LpdFemGui import *
from utilities import *
import time
import sys
from functools import partial

class LpdFemGuiMainConfigTab(object):
    '''
    Helper class to manage FEM config tab in main window
    '''


    def __init__(self, app_main, mainWindow):
        '''
        Constructor
        '''
        self.app_main = app_main
        self.mainWindow = mainWindow
        self.ui = mainWindow.ui
        self.msgPrint = self.mainWindow.msgPrint

        # Connect signals and slots for FEM config tab
        QtCore.QObject.connect(self.ui.configUpdateButton, QtCore.SIGNAL("clicked()"), self.updateConfig)
        
        
    def showConfig(self):
        
        self.ui.magicNumber.setText('0x%X' % self.app_main.femConfig.magicWord)
        self.ui.checksum.setText('0x%X' % self.app_main.femConfig.checksum)
        self.ui.macAddress.setText(self.app_main.femConfig.net_mac_str())
        self.ui.ipAddress.setText(self.app_main.femConfig.net_ip_addr_str())
        self.ui.netMask.setText(self.app_main.femConfig.net_ip_mask_str())
        self.ui.gateway.setText(self.app_main.femConfig.net_ip_gw_str())
        self.ui.highTempThreshold.setText(str(self.app_main.femConfig.temp_high))
        self.ui.critTempTreshold.setText(str(self.app_main.femConfig.temp_crit))
        self.ui.boardId.setText(str(self.app_main.femConfig.board_id))
        self.ui.boardType.setText(str(self.app_main.femConfig.board_type))
        self.ui.hwVersionMajor.setText(str(self.app_main.femConfig.hw_major_version))
        self.ui.hwVersionMinor.setText(str(self.app_main.femConfig.hw_minor_version))
        self.ui.fwVersionMajor.setText(str(self.app_main.femConfig.fw_major_version))
        self.ui.fwVersionMinor.setText(str(self.app_main.femConfig.fw_minor_version))
        self.ui.swVersionMajor.setText(str(self.app_main.femConfig.sw_major_version))
        self.ui.swVersionMinor.setText(str(self.app_main.femConfig.sw_minor_version))
        
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
        
        self.app_main.femConfigUpdate(net_mac, net_ip, net_mask, 
                        net_gw, temp_high, temp_crit, 
                        sw_major, sw_minor, fw_major, fw_minor,
                        hw_major, hw_minor, board_id, board_type)
        
        self.msgPrint("Reading configuration back")
        self.app_main.femConfigGet()
        self.showConfig()
        