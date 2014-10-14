from PyQt4 import QtCore
import sys, serial

class AsyncExecutionThread(QtCore.QThread):
    
    executionComplete = QtCore.pyqtSignal()
    
    def __init__(self, execCmd, doneCmd):
        QtCore.QThread.__init__(self)
        self.execCmd = execCmd
        self.doneCmd = doneCmd

    def run(self):
        
        self.executionComplete.connect(self.doneCmd)
        self.execCmd()
        self.executionComplete.emit()
        
def checkButtonState(state):
    
    if state == True:
        qtState = QtCore.Qt.Checked
    elif state == False:
        qtState = QtCore.Qt.Unchecked
    else:
        qtState = QtCore.Qt.Unchecked
        
    return qtState

        
def validIpAddress(address):
    parts = address.split(".")
    if len(parts) != 4:
        return False
    try:
        for item in parts:
            if not 0 <= int(item) <= 255:
                return False
    except:
        return False
    
    return True

def validPort(port):
    
    try:
        if not 0 <= int(port) <= 65535:
            return False
    except:
        return False
    
    return True

