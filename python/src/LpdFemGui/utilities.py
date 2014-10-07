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


class servoShutter():
    ''' Class to control Arduino shutter for Diamond beam time '''
    
    def __init__(self, usbport):
        # Set up serial baud rate
        try:
            self.ser = serial.Serial(usbport, 9600, timeout=1)
            print >> sys.stderr, "Connected to Arduino shutter"
        except Exception as e:
            raise Exception("Serial Connection Error: %s" % e)

    def __del__(self):
        # Close serial connection, if open
        try:
            if self.ser.isOpen():
                self.ser.close()
        except Exception:
            # Suppress any error upon exit
            pass
        
    def move(self, position):
        ''' Moves the shutter to the supplied position
            0=shut, 1=open '''

        if (0 <= position <= 1):
            try:
                self.ser.write(chr(position))
            except Exception as e:
                raise Exception("Error %s shutter: %s" % (("closing" if position is 0 else "opening"), e))
            print >> sys.stderr, "Exercising the shutter by %s it.." % (("closing" if position is 0 else "opening"))
        else:
            raise Exception("Shutter position must be an integer, either 0 (shut) or 1 (open)")

