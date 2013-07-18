'''
Created on Jun 13, 2013

    Trying to merge LpdUniViewWindow's functionality into a QMainWindow derived class
    
    Pinched from: http://stackoverflow.com/questions/5770263/segfault-using-matplotlib-with-pyqt

This demo demonstrates how to embed a matplotlib (mpl) plot 
into a PyQt4 GUI application, including:

* Using the navigation toolbar
* Adding data to the plot
* Dynamically modifying the plot's properties
* Processing mpl events
* Saving the plot to a file from a menu

@author: ckd27546 (well, mostly pinched from Eli Bendersky of the tinternet-web thingy..)
'''

from LpdFemGui.LpdDataContainers import LpdImageContainer

from LpdUniReceive import *

import sys, os, LpdFemGui.utilities
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import numpy as np

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure


class LpdUniPlotData(QMainWindow):

    liveViewUpdateSignal = pyqtSignal(object)
    
    matplotlib.rcParams.update({'font.size': 8})
    
    def __init__(self, parent=None, asicModuleType=0):
        
        QMainWindow.__init__(self, parent)
        
        if asicModuleType == FrameProcessor.AsicTypeSuperModule:
            moduleType = "Super Module"
        elif asicModuleType == FrameProcessor.AsicTypeSingleAsic:
            moduleType = "[single ASIC not yet implemented!]"
        elif asicModuleType == FrameProcessor.AsicTypeTwoTile:
            moduleType = "2-Tile System"
        elif asicModuleType == FrameProcessor.AsicTypeAloneFem:
            moduleType = "[stand-alone fem not yet implemented!]"
        elif asicModuleType == FrameProcessor.AsicTypeRawData:
            moduleType = "Super Module [Raw Data]"
        self.setWindowTitle('Plotting data from %s' % moduleType)

        self.asicModuleType = asicModuleType

        #setup rows and cols according asicModuleType, to pass onto LpdUniPlotData instance
        if self.asicModuleType == FrameProcessor.AsicTypeSuperModule:
            self.nrows = 32*8   # 32 rows * 8 ASICs = 256 
            self.ncols = 256    # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors / Row: 16 x 8 x 2 = 256 columns
        elif self.asicModuleType == FrameProcessor.AsicTypeSingleAsic:
            self.nrows = 32     # 32 rows
            self.ncols = 16     # 16 columns
        elif self.asicModuleType == FrameProcessor.AsicTypeTwoTile:
            self.nrows = 32     # 32 rows
            self.ncols = 256    # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors / Row: 16 x 8 x 2 = 256 columns
        elif self.asicModuleType == FrameProcessor.AsicTypeAloneFem:
            self.nrows = 32     # 32 rows
            self.ncols = 128    # 16 columns/ASIC, 8 ASICs / sensor: 16 x 8 = 128 columns
        if self.asicModuleType == FrameProcessor.AsicTypeRawData:
            self.nrows = 256    # 32 rows * 8 ASICs = 256 
            self.ncols = 256    # 16 columns/ASIC, 8 ASICs / sensor, 2 sensors / Row: 16 x 8 x 2 = 256 columns
            
        self.imageSize = self.nrows * self.ncols

        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()

#        self.textbox.setText('1 2 3 4')
        self.on_draw()

        # Connect the live view update signal
        self.liveViewUpdateSignal.connect(self.liveViewUpdate)

    def liveViewUpdate(self, lpdImage):

        try:
            # Mask off gain bits
            lpdImage.imageArray = lpdImage.imageArray & 0xfff
            self.imgObject.set_data(lpdImage.imageArray)
            self.axes.draw_artist(self.imgObject)
            self.axes.set_title("Train %d Image %d" % ( lpdImage.frameNumber, lpdImage.imageNumber))
            self.canvas.draw()
        except Exception as e:
            print "liveViewUpdate() Error: ", e

    def save_plot(self):
        file_choices = "PNG (*.png)|*.png"

        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save file', '', 
                        file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)

    def on_about(self):
        msg = """ A unified readout of LPD detectors
        * Currently it supports reading out 2-Tile System and Super Module
        
        Developed by ckd27546 for the European XFEL, LPD project
        """
        QMessageBox.about(self, "About the Gui", msg.strip())

#    def on_pick(self, event):
#        # The event received here is of the type
#        # matplotlib.backend_bases.PickEvent
#        #
#        # It carries lots of information, of which we're using
#        # only a small amount here.
#        # 
#        box_points = event.artist.get_bbox().get_points()
#        msg = "You've clicked on a bar with coords:\n %s" % box_points
#
#        QMessageBox.information(self, "Click!", msg)

    def on_draw(self):
        """ Redraws the figure
        """

        self.canvas.draw()

    def create_main_frame(self):
        self.main_frame = QWidget()

        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = Figure((8.0, 6.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)

        # Since we have only one plot, we can use add_axes 
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #
        self.axes = self.fig.add_subplot(111)

        # Disable up the X and Y ticks
        self.axes.set_xticks([])
        self.axes.set_yticks([])


        # Create an empty plot
        self.data = np.zeros((self.nrows, self.ncols), dtype=np.uint16)                   
        self.imgObject = self.axes.imshow(self.data, interpolation='nearest', vmin='0', vmax='4095')

        # Position colorbar according to selected Asic Module Type
        if self.asicModuleType == 2:
            # 2-Tile: horizontal
            cBarPosn = 'horizontal'
        else:
            # Super Module, etc: vertical 
            cBarPosn = 'vertical'
        
        # Create nd show a colourbar
        axc, kw = matplotlib.colorbar.make_axes(self.axes, orientation=cBarPosn)
        cb = matplotlib.colorbar.Colorbar(axc, self.imgObject, orientation=cBarPosn)
        self.imgObject.colorbar = cb

        # Add lines according to module type
        if self.asicModuleType == FrameProcessor.AsicTypeTwoTile:
            # Two Tile System
             
            # Add vertical lines to differentiate between the ASICs
            for i in range(16, self.ncols, 16):
                self.axes.vlines(i-0.5, 0, self.nrows-1, color='b', linestyles='solid')
            
            # Add vertical lines to differentiate between the two tiles
            self.axes.vlines(128-0.5, 0, self.nrows-1, color='y', linestyle='solid')
            
        elif self.asicModuleType == FrameProcessor.AsicTypeSuperModule:
                # Super Module
                
                # Add vertical lines to differentiate between the ASICs
                for i in range(16, self.ncols, 16):
                    self.axes.vlines(i-0.5, 0, self.nrows-1, color='b', linestyles='solid')
                
                # Add vertical lines to differentiate between tiles
                self.axes.vlines(128-0.5, 0, self.nrows-1, color='y', linestyle='solid')
                
                for i in range(32, self.nrows, 32):
                    self.axes.hlines(i-0.5, 0, self.nrows-1, color='y', linestyles='solid')

        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        #
        # Layout with box sizers
        # 
        hbox = QHBoxLayout()

        vbox = QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addLayout(hbox)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

    def create_status_bar(self):
        self.status_text = QLabel("This is the status bar")
        self.statusBar().addWidget(self.status_text, 1)

    def create_menu(self):        
        self.file_menu = self.menuBar().addMenu("&File")

        load_file_action = self.create_action("&Save plot",
            shortcut="Ctrl+S", slot=self.save_plot, 
            tip="Save the plot")
        quit_action = self.create_action("&Quit", slot=self.close, 
            shortcut="Ctrl+Q", tip="Close the application")

        self.add_actions(self.file_menu, 
            (load_file_action, None, quit_action))

        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip='About the demo')

        self.add_actions(self.help_menu, (about_action,))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = LpdUniPlotData()
    form.show()
    app.exec_()