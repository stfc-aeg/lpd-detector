'''
Created on 21 Oct 2011

@author: ckd27546
'''
import sys, Queue
from PyQt4 import QtGui, QtCore
from excaliburPowerGuiMain_ui import Ui_mainWindow

class ExcaliburPowerGuiMain(QtGui.QMainWindow):

    def __init__(self, queue, endcommand, *args):

        self.queue = queue
        self.endcommand = endcommand
        
#        # Set up the GUI part
        QtGui.QMainWindow.__init__(self)
        self.gui = Ui_mainWindow()
        self.gui.setupUi(self)
        
    def closeEvent(self, ev):
        self.endcommand()

    def processIncoming(self):
        """
        Handle all the messages currently in the queue (if any).
        """
        while self.queue.qsize():
            try:
                # Receive message from queue, e.g. "leHum_mon=23.3125"
                msg = self.queue.get(0)
                # Check contents of message and do what it says
                # As a test, we simply print it
                # Split string into GUI component and value
                cmdList = msg.split("=")
                # Check for special cases
                if cmdList[0].find("hideGuiBars") is not -1:
                    self.hideGuiProgressAndStatusBars()
                else:
                    # cmdList[0] is string containing GUI component, e.g. "leHum_mon"
                    # cmdList[1] is string containing it's value, e.g. "23.3125"
                    #--------
                    # Construct dispatch function in situ..
                    try:
                        # path to component...
                        guiComponent = getattr(self.gui, "%s" % cmdList[0])
#                        print cmdList[0], cmdList[1]

                        # Component located ok
                        try:
                            
                            # ...then it's .setText() function
                            handlerMethod = getattr(guiComponent, "setText")
                        except AttributeError:
                            #  Not a QLineEdit object (or object lacking setTest() function..)                            
                            try:
                                # Is this a LED component?
                                handlerMethod = getattr(guiComponent, "setStyleSheet")
                                # e.g.: self.gui.gui.frmHumidityStatus.setStyleSheet()
                            except:
                                # Nope, unknown Gui Component
                                print "Error: Gui component \"", guiComponent, "\" neither QLineEdit nor LED type!"
                            else:
                                try:
                                    # Found setStyleSheet() attribute, now construct it's argument
                                    argumentValue = QtCore.QString.fromUtf8( str( cmdList[1] ))
                                    # e.g.: argumentsValue = QtCore.QString.fromUtf8("\nbackground-color: rgb(0, 255, 0);")
                                    try:
                                        # Call function with argument
                                        handlerMethod( argumentValue )
                                        # e.g.: self.gui.gui.frmHumidityStatus.setStyleSheet(QtCore.QString.fromUtf8("\nbackground-color: rgb(0, 255, 0);"))
                                    except:
                                        # Failed, reason unknown
                                        print "Couldn't update LED component, reason unknown"
                                        
                                except:
                                    # Could not construct argumentValue
                                    print "Could not construct argument for setStyleSheet function!"

                        else:
                            # QEditLine handlerMethod function complete, call with argument
                            handlerMethod(str(cmdList[1]))
                    except:
                        # Gui component not found
                        print "Gui Component doesn't exist: a typo maybe?"

            except Queue.Empty:
                pass


    def hideGuiProgressAndStatusBars(self):
        # I2C devices initialised, hide status bar and progress bar
        self.progressBar.hide()
        self.statusBar().hide()


#    def do_leHum_mon(self, guiComponent, value):
#        """ Dispatch function lm92 """
#        try:
#            # Locate the QLineEdit component in question ..
#            handlerGuiMethod = getattr(self.gui, "%s" % guiComponent)
#            # Then it's .setText() function..
#            handlerGuiMethod = getattr(handlerGuiMethod, "setText")
#        except AttributeError:
#            # A typo along the way
#            print "Error with handlerGuiMethod!"
#        else:
#            # All went well, update said component
#            handlerGuiMethod(str(value))
#
#        
#    def do_leHum_stat(self, guiComponent, value):
#        """ Dispatch function tmp275 """
#        try:
#            # Locate the QLineEdit component in question ..
#            handlerGuiMethod = getattr(self.gui, "%s" % guiComponent)
#            # Then it's .setText() function..
#            handlerGuiMethod = getattr(handlerGuiMethod, "setText")
#        except AttributeError:
#            # A typo along the way
#            print "Error with handlerGuiMethod!"
#        else:
#            # All went well, update said component
#            handlerGuiMethod(str(value))



            
#def do_lePollingInterval(self, value): pass
#def do_leDebugOutput(self, value): pass
#def do_leDebugInput(self, value): pass
#def do_le5VAV(self, value): pass
#def do_le5VAA(self, value): pass
#def do_le5VBV(self, value): pass
#def do_le5VBA(self, value): pass
#def do_le5VCV(self, value): pass
#def do_le5VCA(self, value): pass
#def do_le18VAV(self, value): pass
#def do_le18VAA(self, value): pass
#def do_le18VBV(self, value): pass
#def do_le18VBA(self, value): pass
#def do_le18VCV(self, value): pass
#def do_le18VCA(self, value): pass
#def do_le33VV(self, value): pass
#def do_le33VA(self, value): pass
#def do_le200VV(self, value): pass
#def do_le200VA(self, value): pass
#def do_le48VV(self, value): pass
#def do_le48VA(self, value): pass
#def do_le5SUPERVV(self, value): pass
#def do_le5SUPERVA(self, value): pass
#def do_leHum_stat(self, value): pass
#def do_leAirtmp_mon(self, value): pass
#def do_leAirtmp_mon_2(self, value): pass
#def do_leWatertmp_mon(self, value): pass
#def do_leWatertmp_stat(self, value): pass
#def do_leCoolant_stat(self, value): pass
#def do_leCoolant_temp_stat(self, value): pass
#def do_le200V_ONOFF(self, value): pass
#def do_leBias_Level(self, value): pass


    def displayErrorMessage(self, errorString):
        """ Constructs a string from errorString and the other argument(s) (if provided),
            displaying this in the GUI and print it to console """
        errorMsg = errorString + str(sys.exc_info()[0]) + str(sys.exc_info()[1])
        self.msgPrint( errorMsg )


    def msgPrint(self, msg, term='\n'):
        """ Put msg (error) string into mbErrorMessages (TextField) """
        self.gui.mbErrorMessages.insertPlainText(str(msg) + term)
#        self.gui.gui.mbErrorMessages.repaint()
        self.app.processEvents()
#        self.ui.mbErrorMessages.insertPlainText(str(msg) + term)
#        self.ui.mbErrorMessages.repaint()
#        self.guiMain.app.processEvents()
