'''
Created on Apr 22, 2013

@author: tcn45
'''
from __future__ import print_function

from LpdDataContainers import LpdImageContainer
from LpdFemClient.LpdFemClient import LpdFemClient

from PyQt4 import QtCore, QtGui
from utilities import *
import sys

import numpy as np

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class LpdFemGuiLiveViewWindow(QtGui.QDialog):
    
    liveViewUpdateSignal = QtCore.pyqtSignal(object)
    
    matplotlib.rcParams.update({'font.size': 8})
    
    def __init__(self, parent=None, asicModuleType=0):
 
        QtGui.QDialog.__init__(self, parent)

        self.asicModuleType = asicModuleType

        # Set nrows, ncols and moduleType according asicModuleType
        if self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_SUPER_MODULE:
            moduleType = "Super Module"
            self.nrows = 256 
            self.ncols = 256
        elif self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_TWO_TILE:
            moduleType = "2-Tile System"
            self.nrows = 32
            self.ncols = 256
        elif self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_RAW_DATA:
            moduleType = "Super Module [Raw Data]"
            self.nrows = 256 
            self.ncols = 256
        else:
            print("Error: Unsupported asicModuleType selected: %r" % self.asicModuleType, file=sys.stderr)
        
        self.setWindowTitle('Plotting data from %s' % moduleType)

        self.plotFrame =QtGui.QWidget()
        
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = Figure((8.0, 6.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.plotFrame)
        
        # Since we have only one plot, we can use add_axes 
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #
        self.axes = self.fig.add_subplot(111)
 
        # Disable up the X and Y ticks
        self.axes.set_xticks([])
        self.axes.set_yticks([])
       
        self.imageSize = self.nrows * self.ncols

        # Create an empty plot
        self.data = np.zeros((self.nrows, self.ncols), dtype=np.uint16)                   
        self.imgObject = self.axes.imshow(self.data, interpolation='nearest', vmin=0, vmax=4095)

        # Position colorbar according to selected asicModuleType
        if self.asicModuleType == 2:
            cBarPosn = 'horizontal'
            # Place 2-Tile plot closer to center of figure
            self.axes.set_position([0.125, 0.4, 0.8, 0.5])
        else: 
            cBarPosn = 'vertical'

        # Create nd show a colourbar
        axc, kw = matplotlib.colorbar.make_axes(self.axes, orientation=cBarPosn)
        cb = matplotlib.colorbar.Colorbar(axc, self.imgObject, orientation=cBarPosn)
        # Fix: Re-adjust tick marks along colour bar:
        cTicks = [0, 511, 1023, 1535, 2047, 2559, 3071, 3583, 4095]
        cb.set_ticks(ticks=cTicks, update_ticks=True)
        self.imgObject.colorbar = cb

        # Add lines according to module type
        if self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_TWO_TILE:
             
            # Add vertical lines to differentiate between the ASICs
            for i in range(16, self.ncols, 16):
                self.axes.vlines(i-0.5, 0, self.nrows-1, color='b', linestyles='solid')
            
            # Add vertical lines to differentiate between the two tiles
            self.axes.vlines(128-0.5, 0, self.nrows-1, color='y', linestyle='solid')
            
        elif self.asicModuleType == LpdFemClient.ASIC_MODULE_TYPE_SUPER_MODULE:
                
                # Add vertical lines to differentiate between the ASICs
                for i in range(16, self.ncols, 16):
                    self.axes.vlines(i-0.5, 0, self.nrows-1, color='b', linestyles='solid')
                
                # Add vertical lines to differentiate between tiles
                self.axes.vlines(128-0.5, 0, self.nrows-1, color='y', linestyle='solid')
                
                for i in range(32, self.nrows, 32):
                    self.axes.hlines(i-0.5, 0, self.nrows-1, color='y', linestyles='solid')


        self.canvas.draw()

        # Bind the 'pick' event for clicking on one of the bars
        #
        #self.canvas.mpl_connect('pick_event', self.on_pick)
        
        # Create the navigation toolbar, tied to the canvas
        #
        self.mplToolbar = NavigationToolbar(self.canvas, self.plotFrame)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.mplToolbar)
        vbox.addWidget(self.canvas)
        
        self.setLayout(vbox)
        
        self.setWindowTitle("Live View")
        self.setModal(False)
        
        # Connect the live view update signal
        self.liveViewUpdateSignal.connect(self.liveViewUpdate)
        
    def closeEvent(self, event):
        event.accept()
        
    def liveViewUpdate(self, lpdImage):
        
        # Mask off gain bits
        lpdImage.imageArray = lpdImage.imageArray & 0xfff
        self.imgObject.set_data(lpdImage.imageArray)
        self.axes.draw_artist(self.imgObject)
        self.axes.set_title("Run %d Train %d Image %d" % (lpdImage.runNumber, lpdImage.frameNumber, lpdImage.imageNumber))
        self.canvas.draw()
