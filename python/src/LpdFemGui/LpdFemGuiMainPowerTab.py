'''
Created on Apr 19, 2013

@author: tcn45
'''

from __future__ import print_function
from PyQt4 import QtCore, QtGui
from LpdFemGuiMainWindow_ui import Ui_MainWindow
from LpdFemGui import *
from utilities import *
import time
import sys
from functools import partial

class LpdFemGuiMainPowerTab(object):
    '''
    Helper class to manage power tab in main window
    '''
        
    def __init__(self, app_main, mainWindow):
        
        self.app_main = app_main
        self.mainWindow = mainWindow
        self.ui = mainWindow.ui
        self.msgPrint = self.mainWindow.msgPrint
        
        # Initialise default fields based on app_main cached parameters    
        self.ui.hvBiasEdit.setText(str(self.app_main.getCachedParam('hvBiasVolts')))
        self.autoUpdate = self.app_main.getCachedParam('pwrAutoUpdate')
        autoUpdateState = QtCore.Qt.Checked if self.autoUpdate == True else QtCore.Qt.Unchecked
        self.ui.pwrAutoUpdateSel.setCheckState(autoUpdateState)
        self.ui.pwrUpdateIntervalEdit.setText(str(self.app_main.getCachedParam('pwrUpdateInterval')))
        
        # Connect signals and slots
        QtCore.QObject.connect(self.ui.lvEnableBtn,     QtCore.SIGNAL("clicked()"), self.lvEnableToggle)
        QtCore.QObject.connect(self.ui.hvEnableBtn,     QtCore.SIGNAL("clicked()"), self.hvEnableToggle)
        QtCore.QObject.connect(self.ui.hvBiasSetBtn,    QtCore.SIGNAL("clicked()"), self.hvBiasSetUpdate)
        QtCore.QObject.connect(self.ui.pwrAutoUpdateSel, QtCore.SIGNAL("toggled(bool)"), self.pwrAutoUpdateSelect)
        QtCore.QObject.connect(self.ui.pwrUpdateIntervalEdit, QtCore.SIGNAL("editingFinished()"), self.pwrUpdateIntervalUpdate)
        QtCore.QObject.connect(self.ui.pwrUpdateBtn,    QtCore.SIGNAL("clicked()"), self.powerStatusUpdate)

    def updateEnabledWidgets(self):
        
        if self.app_main.device_state == LpdFemGui.DeviceDisconnected:
            self.ui.pwrControlGroupBox.setEnabled(False)
            self.ui.pwrMonitorGroupBox.setEnabled(False)
        else:
            self.ui.pwrControlGroupBox.setEnabled(True)
            self.ui.pwrMonitorGroupBox.setEnabled(True)
            
    def lvEnableToggle(self):
        
        currentState = self.app_main.pwr_card.lvEnableGet()        
        nextState = not currentState
        actionMsg = "Enabling" if nextState == True else "Disabling"
        self.mainWindow.executeAsyncCmd('%s low voltage' % actionMsg, partial(self.app_main.pwr_card.lvEnableSet, nextState), 
                              partial(self.lvEnableToggleDone, nextState))
                    
    def lvEnableToggleDone(self, requestedState=None):

        stateNow = self.app_main.pwr_card.lvEnableGet()
        if requestedState != None and stateNow != requestedState:
            self.msgPrint("ERROR: failed to switch LV enable to %d" % requestedState)
        else:
            self.powerBtnStateUpdate('lv', stateNow)
        self.powerStatusUpdateDone()
    
    def hvEnableToggle(self):

        currentState = self.app_main.pwr_card.hvEnableGet()        
        nextState = not currentState
        actionMsg = "Enabling" if nextState == True else "Disabling"
        self.mainWindow.executeAsyncCmd('%s high voltage' % actionMsg, partial(self.app_main.pwr_card.hvEnableSet, nextState),
                             partial(self.hvEnableToggleDone, nextState))
        
    def hvEnableToggleDone(self, requestedState = None):
    
        stateNow = self.app_main.pwr_card.hvEnableGet()
        if requestedState != None and  stateNow != requestedState:
            self.msgPrint("ERROR: failed to switch HV enable to %d" % requestedState)
        else:
            self.powerBtnStateUpdate('hv', stateNow)
        self.powerStatusUpdateDone()
   
    def hvBiasSetUpdate(self):
        
        biasStr = self.ui.hvBiasEdit.text()
        try:
            hvBias = float(biasStr)
            self.app_main.setCachedParam('hvBiasVolts', hvBias)
            self.mainWindow.executeAsyncCmd('Setting HV bias to {:.1f} V'.format(hvBias), partial(self.app_main.pwr_card.hvBiasSet, hvBias), self.hvBiasSetDone)
            
        except ValueError:
            self.msgPrint("Illegal value entered for HV bias: %s" % biasStr)
            self.ui.hvBiasEdit.setText(str(self.app_main.getCachedParam('hvBiasVolts')))
            
    def hvBiasSetDone(self):

        self.powerStatusUpdateDone()        
        self.msgPrint("HV bias set complete")
    
    def pwrAutoUpdateSelect(self, state):
        self.msgPrint("Power auto update select set to %d" % int(state))
        self.app_main.setCachedParam('pwrAutoUpdate', state)
        self.autoUpdate = state
        
        if self.autoUpdate == True:
            self.autoUpdateThread = PowerAutoUpdateThread(self.app_main, self)
            self.autoUpdateThread.start()
        
    def pwrUpdateIntervalUpdate(self):
        pwrUpdateInterval = self.ui.pwrUpdateIntervalEdit.text()
        try:
            pwrUpdateIntervalVal = int(pwrUpdateInterval)
            self.app_main.setCachedParam('pwrUpdateInterval', pwrUpdateIntervalVal)
        except ValueError:
            self.ui.pwrUpdateIntervalEdit.setText(str(self.app_main.getCachedParam('pwrUpdateInterval')))
            
    def powerStatusUpdate(self):
        
        self.mainWindow.executeAsyncCmd('Updating power status...', self.app_main.pwr_card.statusUpdate, self.powerStatusUpdateDone)
        
    def powerStatusUpdateDone(self):
        
        self.mainWindow.powerStatusSignal.emit(self.app_main.pwr_card.powerStateGet())

    def powerStatusUpdateDisplay(self, powerState):
        
        powerCardName = ('lhs', 'rhs')
        sensorParamList = ('Temp', 'Volt', 'Cur')
        powerCardParams = {'powerCardTemp'     : 'PsuTemp',
                           'femVoltage'        : 'FemVolt',
                           'femCurrent'        : 'FemCur',
                           'digitalVoltage'    : 'DigitalVolt',
                           'digitalCurrent'    : 'DigitalCur',
                           'sensorBiasVoltage' : 'BiasVolt', 
                           'sensorBiasCurrent' : 'BiasCur'
                           }
        powerCardFlags = { 'asicPowerEnable'      : 'LvStatus',
                           'sensorBiasEnable'     : 'HvStatus',
                           'powerCardFault'       : 'FaultFlag',
                           'powerCardFemStatus'   : 'FemFlag',
                           'powerCardExtStatus'   : 'ExtFlag',
                           'powerCardOverCurrent' : 'OvCurFlag',
                           'powerCardOverTemp'    : 'OvTempFlag',
                           'powerCardUnderTemp'   : 'UnTempFlag',
                           }
        
        # Loop over LHS and RHS power cards and update display
        for powerCard in range(self.app_main.pwr_card.numPowerCards):
            
            # Update flags
            for paramStem, uiObjStem in list(powerCardFlags.items()):
                
                paramName = paramStem + str(powerCard)
                uiObjName= powerCardName[powerCard] + uiObjStem
                
                try:
                    uiObj = getattr(self.ui, uiObjName)
                    if paramStem == 'asicPowerEnable' or paramStem == 'sensorBiasEnable':
                        powerStateVal = 'Yes' if powerState[paramName] == 0 else 'No'
                    else:
                        powerStateVal = powerState[paramName]
                    self.updateFlag(uiObj, powerStateVal)
                except Exception as e:
                    print("Exception during UI object mapping: %s" % e, file=sys.stderr)
                    
            # Update sensor bias
            paramName = 'sensorBias' + str(powerCard)
            uiObjName = powerCardName[powerCard] + 'BiasSetpoint'
            try:
                uiObj = getattr(self.ui, uiObjName)
                uiObj.setText("{:.1f}".format(powerState[paramName]))
            except Exception as e:
                print("Exception during UI object mapping: %s" % e, file=sys.stderr)
            
            # Update sensor parameters
            for sensor in range(self.app_main.pwr_card.numSensorsPerCard):
                sensorIdx = sensor + ( powerCard * self.app_main.pwr_card.numSensorsPerCard)
                for (param, uiParam) in zip(self.app_main.pwr_card.sensorParamList, sensorParamList):
                    paramName = 'sensor' + str(sensorIdx) + param
                    uiObjName = powerCardName[powerCard] + 'Sensor' + uiParam + str(sensor)
                    try:
                        uiObj = getattr(self.ui, uiObjName)
                        uiObj.setText("{:.2f}".format(powerState[paramName]))
                    except Exception as e:
                        print("Exception during UI object mapping: %s" % e, file=sys.stderr)
            
            # Update power card parameters
            for paramStem, uiObjStem in list(powerCardParams.items()):
                
                paramName = paramStem + str(powerCard)
                uiObjName   = powerCardName[powerCard] + uiObjStem
                try:
                    uiObj = getattr(self.ui, uiObjName)
                    uiObj.setText("{:.2f}".format(powerState[paramName]))
                except Exception as e:
                    print("Exception during UI object mapping: %s" % e, file=sys.stderr)
                    
        timeStr = time.strftime("%H:%M:%S")
        self.ui.lastUpdate.setText(timeStr)
        
    def powerBtnStateUpdate(self, whichBtn, state):
        
        if whichBtn == 'lv':
            btn = self.ui.lvEnableBtn
            stateDisp = self.ui.lvStatus
        elif whichBtn == 'hv':
            btn = self.ui.hvEnableBtn
            stateDisp = self.ui.hvStatus
        else:
            return
        
        buttonText = "Disable" if state == True else "Enable"
        stateText  = "ON" if state == True else "OFF"
        btn.setText(buttonText)
        stateDisp.setText(stateText)

    def updateFlag(self, uiObj, value):
        
        if value == "Yes" or value == True:
            bgColour = "rgb(255, 0, 0)"
        elif value == "No" or value == False:
            bgColour = "rgb(0, 255, 0)"
        else:
            bgColour = "rgb(255, 255, 200)"

        uiObj.setStyleSheet("background-color: %s;" % bgColour)
            
class PowerAutoUpdateThread(QtCore.QThread):
    
    updateDone = QtCore.pyqtSignal()
    
    def __init__(self, app_main, pwrTab):
        QtCore.QThread.__init__(self)
        self.app_main = app_main
        self.pwrTab = pwrTab
        
    def run(self):
        
        print("Starting power card auto monitoring thread")
        self.updateDone.connect(self.pwrTab.powerStatusUpdateDone)
        
        while self.pwrTab.autoUpdate == True and self.app_main.device_state != LpdFemGui.DeviceDisconnected:
            
            #TODO inhibit update loop when device locked
            self.app_main.pwr_card.statusUpdate()
            self.updateDone.emit()
            time.sleep(self.app_main.getCachedParam('pwrUpdateInterval'))
            
        print("Power card auto monitoring thread terminating")
        
