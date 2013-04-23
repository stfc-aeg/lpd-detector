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

class LpdFemGuiMainPowerTab(object):
    '''
    Helper class to manage power tab in main window
    '''
        
    def __init__(self, appMain, mainWindow):
        
        self.appMain = appMain
        self.mainWindow = mainWindow
        self.ui = mainWindow.ui
        self.msgPrint = self.mainWindow.msgPrint
        
    
        # Initialise default fields based on appMain cached parameters    
        self.ui.hvBiasEdit.setText(str(self.appMain.getCachedParam('hvBiasVolts')))
        self.autoUpdate = self.appMain.getCachedParam('pwrAutoUpdate')
        autoUpdateState = QtCore.Qt.Checked if self.autoUpdate == True else QtCore.Qt.Unchecked
        self.ui.pwrAutoUpdateSel.setCheckState(autoUpdateState)
        self.ui.pwrUpdateIntervalEdit.setText(str(self.appMain.getCachedParam('pwrUpdateInterval')))
        
        # Connect signals and slots
        QtCore.QObject.connect(self.ui.lvEnableBtn,     QtCore.SIGNAL("clicked()"), self.lvEnableToggle)
        QtCore.QObject.connect(self.ui.hvEnableBtn,     QtCore.SIGNAL("clicked()"), self.hvEnableToggle)
        QtCore.QObject.connect(self.ui.hvBiasSetBtn,    QtCore.SIGNAL("clicked()"), self.hvBiasSetUpdate)
        QtCore.QObject.connect(self.ui.pwrAutoUpdateSel, QtCore.SIGNAL("toggled(bool)"), self.pwrAutoUpdateSelect)
        QtCore.QObject.connect(self.ui.pwrUpdateIntervalEdit, QtCore.SIGNAL("editingFinished()"), self.pwrUpdateIntervalUpdate)
        QtCore.QObject.connect(self.ui.pwrUpdateBtn,    QtCore.SIGNAL("clicked()"), self.powerStatusUpdate)

    def lvEnableToggle(self):
        
        currentState = self.appMain.pwrCard.lvEnableGet()        
        nextState = not currentState
        actionMsg = "Enabling" if nextState == True else "Disabling"
        self.mainWindow.executeAsyncCmd('%s low voltage' % actionMsg, partial(self.appMain.pwrCard.lvEnableSet, nextState), 
                              partial(self.lvEnableToggleDone, nextState))
                    
    def lvEnableToggleDone(self, nextState):

        if self.appMain.pwrCard.lvEnableGet() != nextState:
            self.msgPrint("ERROR: failed to switch LV enable to %d", nextState)
        else:
            buttonText = "Disable" if nextState == True else "Enable"
            stateText  = "ON" if nextState == True else "OFF"
            self.ui.lvEnableBtn.setText(buttonText)
            self.ui.lvStatus.setText(stateText)
        
    
    def hvEnableToggle(self):

        currentState = self.appMain.pwrCard.hvEnableGet()        
        nextState = not currentState
        actionMsg = "Enabling" if nextState == True else "Disabling"
        self.mainWindow.executeAsyncCmd('%s high voltage' % actionMsg, partial(self.appMain.pwrCard.hvEnableSet, nextState),
                             partial(self.hvEnableToggleDone, nextState))
        
    def hvEnableToggleDone(self, nextState):
    
        if self.appMain.pwrCard.hvEnableGet() != nextState:
            self.msgPrint("ERROR: failed to switch HV enable to %d", nextState)
        else:
            buttonText = "Disable" if nextState == True else "Enable"
            stateText  = "ON" if nextState == True else "OFF"
            self.ui.hvEnableBtn.setText(buttonText)
            self.ui.hvStatus.setText(stateText)
    
    def hvBiasSetUpdate(self):
        
        biasStr = self.ui.hvBiasEdit.text()
        try:
            hvBias = float(biasStr)
            self.appMain.setCachedParam('hvBiasVolts', hvBias)
            self.mainWindow.executeAsyncCmd('Setting HV bias to {:.1f} V'.format(hvBias), partial(self.appMain.pwrCard.hvBiasSet, hvBias), self.hvBiasSetDone)
            
        except ValueError:
            self.msgPrint("Illegal value entered for HV bias: %s" % biasStr)
            self.ui.hvBiasEdit.setText(str(self.appMain.getCachedParam('hvBiasVolts')))
            
    def hvBiasSetDone(self):
        
        self.msgPrint("HV bias set complete")
    
    def pwrAutoUpdateSelect(self, state):
        self.msgPrint("Power auto update select set to %d" % int(state))
        self.appMain.setCachedParam('pwrAutoUpdate', state)
        self.autoUpdate = state
        
        if self.autoUpdate == True:
            self.autoUpdateThread = PowerAutoUpdateThread(self.appMain, self)
            self.autoUpdateThread.start()
        
    def pwrUpdateIntervalUpdate(self):
        pwrUpdateInterval = self.ui.pwrUpdateIntervalEdit.text()
        try:
            pwrUpdateIntervalVal = int(pwrUpdateInterval)
            self.appMain.setCachedParam('pwrUpdateInterval', pwrUpdateIntervalVal)
        except ValueError:
            self.ui.pwrUpdateIntervalEdit.setText(str(self.appMain.getCachedParam('pwrUpdateInterval')))
            
    def powerStatusUpdate(self):
        
        self.mainWindow.executeAsyncCmd('Updating power status...', self.appMain.pwrCard.statusUpdate, self.powerStatusUpdateDone)
        
    def powerStatusUpdateDone(self):
        
        print "DEBUG Power status update done"
        

class PowerAutoUpdateThread(QtCore.QThread):
    
    updateDone = QtCore.pyqtSignal()
    
    def __init__(self, appMain, pwrTab):
        QtCore.QThread.__init__(self)
        self.appMain = appMain
        self.pwrTab = pwrTab
        
    def run(self):
        
        print "Starting auto update thread"
        self.updateDone.connect(self.pwrTab.powerStatusUpdateDone)
        
        print "Entering loop"
        while self.pwrTab.autoUpdate == True:
            
            #TODO inhibit update loop when device locked
            self.appMain.pwrCard.statusUpdate()
            self.updateDone.emit()
            time.sleep(self.appMain.getCachedParam('pwrUpdateInterval'))
            
        print "Auto update thread terminating"
        
