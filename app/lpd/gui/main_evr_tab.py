
from PyQt4 import QtCore, QtGui
from utilities import *
import time
import sys
from functools import partial

class LpdFemGuiMainEvrTab(object):
    '''
    Helper class to manage EVR tab in main window
    '''

    def __init__(self, app_main, mainWindow):
        '''
        Constructor
        '''
        self.app_main = app_main
        self.mainWindow = mainWindow
        self.ui = mainWindow.ui
        self.msgPrint = self.mainWindow.msgPrint

        # Initialise default fields based on app_main object cached parameters
        self.ui.evrMcastGroupEdit.setText(self.app_main.getCachedParam('evrMcastGroup'))
        self.ui.evrMcastPortEdit.setText(str(self.app_main.getCachedParam('evrMcastPort')))
        self.ui.evrMcastInterfaceEdit.setText(self.app_main.getCachedParam('evrMcastInterface'))
        if self.app_main.getCachedParam('evrRecordEnable') == True:
            self.ui.evrRecordEnableSel.setCheckState(QtCore.Qt.Checked)
        else:
            self.ui.evrRecordEnableSel.setCheckState(QtCore.Qt.Unchecked)

                                         
        # Connect signals and slots
        QtCore.QObject.connect(self.ui.evrMcastGroupEdit, QtCore.SIGNAL("editingFinished()"), self.evrMcastGroupUpdate)
        QtCore.QObject.connect(self.ui.evrMcastPortEdit, QtCore.SIGNAL("editingFinished()"), self.evrMcastPortUpdate)
        QtCore.QObject.connect(self.ui.evrMcastInterfaceEdit, QtCore.SIGNAL("editingFinished()"), self.evrMcastInterfaceUpdate)
        QtCore.QObject.connect(self.ui.evrRecordEnableSel, QtCore.SIGNAL("toggled(bool)"), self.evrRecordSelect)

    def updateEnabledWidgets(self):
        pass

    def evrMcastGroupUpdate(self):
        evrMcastGroup = self.ui.evrMcastGroupEdit.text()
        try:
            evrMcastGroupStr = str(evrMcastGroup)
            self.app_main.setCachedParam('evrMcastGroup', evrMcastGroupStr)
            self.mainWindow.updateEnabledWidgets()
        except ValueError:
            self.ui.evrMcastGroupEdit.setText(self.app_main.getCachedParam('evrMcastGroup'))

    def evrMcastPortUpdate(self):
        evrMcastPort = self.ui.evrMcastPortEdit.text()
        try:
            evrMcastPortVal = int(evrMcastPort)
            self.app_main.setCachedParam('evrMcastPort', evrMcastPortVal)
            self.mainWindow.updateEnabledWidgets()
        except ValueError:
            self.ui.evrMcastPortEdit.setText(str(self.app_main.getCachedParam('evrMcastPort')))

    def evrMcastInterfaceUpdate(self):
        evrMcastInterface = self.ui.evrMcastInterfaceEdit.text()
        try:
            evrMcastInterfaceStr = str(evrMcastInterface)
            self.app_main.setCachedParam('evrMcastInterface', evrMcastInterfaceStr)
            self.mainWindow.updateEnabledWidgets()
        except ValueError:
            self.ui.evrMcastInterfaceEdit.setText(self.app_main.getCachedParam('evrMcastInterface'))

    def evrRecordSelect(self, state):
        self.app_main.setCachedParam('evrRecordEnable', state)
        self.mainWindow.updateEnabledWidgets()



