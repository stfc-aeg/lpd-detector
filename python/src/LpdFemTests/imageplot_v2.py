from matplotlib import cbook
import matplotlib.pyplot as plt
import matplotlib.text as text
from matplotlib.widgets import Button

import argparse
import numpy as np
import h5py
import matplotlib
import sys, time
from LpdReadoutConfig import *

class imagePlot():
    
    def __init__(self):

        # Ask the user for data file, image, train..
        self.args = parseArgs()
    
        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        # Create the figure and title
        self.fig = plt.figure(1)
        self.ax = self.fig.add_subplot(111)
        self.mainTitle = plt.title("")
        
        # Previous, next buttons inspired by example: matplotlib.org/1.3.1/examples/widgets/buttons.html

        # Previous, Next image buttons..
        decImage = plt.axes([0.85, 0.06, 0.07, 0.045])
        incImage = plt.axes([0.92, 0.06, 0.07, 0.045])    #  [left, bottom, width, height] 
        incrementImg = Button(incImage, '+I')
        incrementImg.on_clicked(self.nextImage)
        decrementImg = Button(decImage, '-I')
        decrementImg.on_clicked(self.prevImage)

        # Previous, Next train buttons..
        decTrain = plt.axes([0.85, 0.005, 0.07, 0.045])
        incTrain = plt.axes([0.92, 0.005, 0.07, 0.045])    #  [left, bottom, width, height] 
        incrementTrain = Button(incTrain, '+T')
        incrementTrain.on_clicked(self.nextTrain)
        decrementTrain = Button(decTrain, '-T')
        decrementTrain.on_clicked(self.prevTrain)

        self.lineColour = self.args.bordercolour
        
        if self.args.border:
            imageData = self.highlightModuleBorders(self.lineColour, imageData)
        
        self.img = self.ax.imshow(imageData, interpolation='nearest', vmin='0', vmax='4095')

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d : %s' % (runNumber, trainNumber, imageNumber, dateStr)
        self.mainTitle.set_text(titleText)

        # Add a colour bar
        axc, kw = matplotlib.colorbar.make_axes(self.ax)
        cb = matplotlib.colorbar.Colorbar(axc, self.img)
        self.img.colorbar = cb

        self.artist = self.fig.get_children()
        
        DataCursor(self.artist[1], imageData, self.args.border)

        plt.show()    
    
    def highlightModuleBorders(self, lineColour, imageData):
        # Insert columns and rows between adjacent ASIC modules
        imageData = np.insert(imageData, 128, values=lineColour, axis=1)
        imageData = np.insert(imageData, 128, values=lineColour, axis=1)
        imageData = np.insert(imageData, 128, values=lineColour, axis=1)
        imageData = np.insert(imageData, 128, values=lineColour, axis=1)
        for loop in range(imageData.shape[0], 0, -32):
            if loop == 256:
                continue    # Not needed
            imageData = np.insert(imageData, loop, values=lineColour, axis=0)
            imageData = np.insert(imageData, loop, values=lineColour, axis=0)
            imageData = np.insert(imageData, loop, values=lineColour, axis=0)
            imageData = np.insert(imageData, loop, values=lineColour, axis=0)
        return imageData

    def nextImage(self, event):

        self.args.image += 1
        # Is current image number now greater than images per train?
        if self.args.image > self.maxImageNumber:
            # Yes. Is current train number = max train number?
            if self.args.train == self.maxTrainNumber:
                # Both image and train maximum reached, start over with first image in first train
                self.args.train = 0
                self.args.image = 0
            else:
                # Image number exceeded but not train number; Increment train and reset image
                self.args.train += 1
                self.args.image = 0

#        print "nextImage, now train: %3i image: %3i" % (self.args.train, self.args.image)
        
        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d : %s' % (runNumber, trainNumber, imageNumber, dateStr)
        self.mainTitle.set_text(titleText)

        if self.args.border:
            imageData = self.highlightModuleBorders(self.lineColour, imageData)
        
        self.img.set_data(imageData)

        DataCursor(self.artist[1], imageData, self.args.border)
        plt.draw()
    
    def prevImage(self, event):

        self.args.image -= 1
        # Is current image number now sub zero?
        if self.args.image < 0:
            # Yes. Is current train number sub zero?
            if self.args.train == 0:
                # Both image and train minimum reached, start over with last image in last train
                self.args.train = self.maxTrainNumber
                self.args.image = self.maxImageNumber
            else:
                # Image number exceeded but not train number; Decrement train and set image to highest in train
                self.args.train -= 1
                self.args.image = self.maxImageNumber

#        print "prevImage, now train: %3i image: %3i" % (self.args.train, self.args.image)
        
        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d : %s' % (runNumber, trainNumber, imageNumber, dateStr)
        self.mainTitle.set_text(titleText)
        
        if self.args.border:
            imageData = self.highlightModuleBorders(self.lineColour, imageData)

        self.img.set_data(imageData)

        DataCursor(self.artist[1], imageData, self.args.border)
        plt.draw()


    def nextTrain(self, event):

        self.args.train += 1
        # Is current train number now greater than number of trains?
        if self.args.train > self.maxTrainNumber:
            # Yes. Start with first train
                self.args.train = 0

#        print "nextTrain, now train: %3i image: %3i" % (self.args.train, self.args.image)
        
        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d : %s' % (runNumber, trainNumber, imageNumber, dateStr)
        self.mainTitle.set_text(titleText)

        if self.args.border:
            imageData = self.highlightModuleBorders(self.lineColour, imageData)

        self.img.set_data(imageData)

        DataCursor(self.artist[1], imageData, self.args.border)
        plt.draw()
    
    def prevTrain(self, event):

        self.args.train -= 1
        # Is current image number now sub zero?
        if self.args.train < 0:
            # Yes. Start over with last train
                self.args.train = self.maxTrainNumber

#        print "prevTrain, now train: %3i image: %3i" % (self.args.train, self.args.image)
        
        (imgOffset, timeStamp, runNumber, trainNumber, imageNumber, imageData) = self.obtainImageWithInfo()

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp))
        titleText = 'Run %d Train %d Image %d : %s' % (runNumber, trainNumber, imageNumber, dateStr)
        self.mainTitle.set_text(titleText)
        
        if self.args.border:
            imageData = self.highlightModuleBorders(self.lineColour, imageData)

        self.img.set_data(imageData)

        DataCursor(self.artist[1], imageData, self.args.border)
        plt.draw()

    def obtainImageWithInfo(self):

        with h5py.File(self.args.fileName, 'r') as hdfFile:
    
            # Read in the train, image counter and timestamp arrays
            trainNumber = hdfFile['/lpd/data/trainNumber'][...]
            imageNumber = hdfFile['/lpd/data/imageNumber'][...]
            timeStamp   = hdfFile['/lpd/data/timeStamp'][...]
    
            # Get max train and image number form arrays
            self.maxTrainNumber = np.amax(trainNumber)
            self.maxImageNumber = np.amax(imageNumber)
    
            # Read in the metadata
            meta = hdfFile['/lpd/metadata']
    
            # Parse the readout configuration XML blob
            readoutConfig = LpdReadoutConfig(meta['readoutParamFile'][0])
            readoutParams = {}
            for (param, val) in readoutConfig.parameters():
                readoutParams[param] = val
    
            # print readoutParams
    
            # Get number of trains from metadata and check array against argument
            numTrains = meta.attrs['numTrains']
            if numTrains != self.maxTrainNumber + 1:
                print "WARNING: mismatch in number of trains between metadata and file"
    
            if self.args.train > self.maxTrainNumber:
                print "ERROR: train number specified (%d) is bigger than maximum in data (%d), quitting" \
                    % (self.args.train, self.maxTrainNumber)
                sys.exit(1)
    
            # Check image number requested in argument is in range too
            if self.args.image > self.maxImageNumber:
                print "ERROR: images number specified (%d) is bigger than maximum in data (%d), quitting" \
                % (self.args.image, self.maxImageNumber)
                sys.exit(1)
    
            # Calculate image offset into array and range check (should be OK)
            imgOffset = (self.args.train * (self.maxImageNumber + 1)) + self.args.image
            if imgOffset > imageNumber.size:
                print "ERROR: calculated image offset (%d) is larger than images stored in data (%d), quitting" \
                % (imgOffset, imageNumber.size)
                sys.exit(1)
    
            # Read in the image array
            t1 = time.time()
            image = hdfFile['/lpd/data/image']
            t2 = time.time()
            imageData = image[imgOffset,:,:]    # Only read in the specified image  
            t3 = time.time()
    
            # Mask off or select gain range from image data
            if self.args.gain == 0:
                imageData[:] = imageData[:] & 0xFFF
    
            # Invert image if specified
            if self.args.invert != None:
                imageData[:] = 4095 - imageData[:]
    
            return (imgOffset, timeStamp[imgOffset], meta.attrs['runNumber'], trainNumber[imgOffset], imageNumber[imgOffset], imageData) 

def parseArgs():

    parser = argparse.ArgumentParser(description="Read and Plot one specific LPD image from an HDF file, into a figure where clicking inside the image will produce pixel coordinates and value.")

    parser.add_argument("fileName", help='Name of HDF5 data file to open')
    parser.add_argument("-t", "--train", type=int, default=0,
        help="Select train number to plot")
    parser.add_argument("-i", "--image", type=int, default=0,
        help="Select image number with train to plot")
    parser.add_argument("--invert", help="Invert image data")
    parser.add_argument("-g", "--gain", type=int, default=0, choices=[0, 1, 10, 100],
        help="Select gain range from image (0=mask off gain bits)")
    parser.add_argument("-b", "--border", type=bool,default=False, choices=[False, True],
                        help="Place border between adjacent ASIC modules")
    parser.add_argument("-bc", "--bordercolour", type=int, default=0,
                        help="Set border colourbetween adjacent ASIC modules (0-4095)")

    args = parser.parse_args()

    return args

# -------           Modified example from stack overflow:                --------- #

class DataCursor(object):
    ''' Modified from example at: http://stackoverflow.com/a/13306887/2903608 '''
    """A simple data cursor widget that displays the x,y location of a
    matplotlib artist when it is selected."""
    def __init__(self, artists, imageData, bordersEnabled, tolerance=5, offsets=(-20, 20), 
                 #template='x: %0.2f\ny: %0.2f\nPxl: %i',
                 template='Column: %i\nRow: %i\nPixel: %i', display_all=False):
        """Create the data cursor and connect it to the relevant figure.
        "artists" is the matplotlib artist or sequence of artists that will be 
            selected. 
        "imageData" is LPD image data for a super module.
        "bordersEnabled" ASIC borders of 4 pixels between adjacent modules?
        "tolerance" is the radius (in points) that the mouse click must be
            within to select the artist.
        "offsets" is a tuple of (x,y) offsets in points from the selected
            point to the displayed annotation box
        "template" is the format string to be used. Note: For compatibility
            with older versions of python, this uses the old-style (%) 
            formatting specification.
        "display_all" controls whether more than one annotation box will
            be shown if there are multiple axes.  Only one will be shown
            per-axis, regardless. 
        """
        self.imageData = imageData
        self.bordersEnabled = bordersEnabled
        self.template = template
        self.offsets = offsets
        self.display_all = display_all
        if not cbook.iterable(artists):
            artists = [artists]
        self.artists = artists
        self.axes = tuple(set(art.axes for art in self.artists))
        self.figures = tuple(set(ax.figure for ax in self.axes))

        self.annotations = {}
        for ax in self.axes:
            self.annotations[ax] = self.annotate(ax)

        for artist in self.artists:
            artist.set_picker(tolerance)
        for fig in self.figures:
            fig.canvas.mpl_connect('pick_event', self)

    def annotate(self, ax):
        """Draws and hides the annotation box for the given axis "ax"."""
        annotation = ax.annotate(self.template, xy=(0, 0), ha='right',
                xytext=self.offsets, textcoords='offset points', va='bottom',
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                )
        annotation.set_visible(False)
        return annotation

    def __call__(self, event):
        """Intended to be called through "mpl_connect"."""
        # Rather than trying to interpolate, just display the clicked coords
        # This will only be called if it's within "tolerance", anyway.
        x, y = event.mouseevent.xdata, event.mouseevent.ydata
        annotation = self.annotations[event.artist.axes]
        if x is not None:
            if not self.display_all:
                # Hide any other annotation boxes...
                for ann in self.annotations.values():
                    ann.set_visible(False)
            # Update the annotation in the current axis..
            annotation.xy = x, y
            # Is borders enabled, update x, y were necessary
            (x_offset, y_offset, pixelValue) = (0, 0, -1)
            if self.bordersEnabled:
                if self.borderValueSelected(x, y):
                    pixelValue = -1
                else:
                    (x_offset, y_offset) = self.adjustCoordByBorders(x, y)
                    pixelValue = self.imageData[y, x]
            else:
                pixelValue = self.imageData[y, x]
            
            annotation.set_text(self.template % (x+x_offset, y+y_offset, pixelValue))
            annotation.set_visible(True)
            event.canvas.draw()
            
    def borderValueSelected(self, x, y):
        """ Check whether the users clicked on one of the borders """
#        print "=========================="
        # Ensure we are using integer values
        (x, y) = int(x), int(y)
        bBorderValueSelected = False
        if x in range(128, 132):
#            print "x within the border!"
            bBorderValueSelected = True
#        else:
#            print "Not xborder, x: ", x, " range: ", range(128, 132)
        
        # Note: Border adds 4 pixels between adjacent ASICs        
        yBorders = [32, 33, 34, 35, 68, 69, 70, 71, 104, 105, 106, 107, 140, 141, 142, 143, 176, 177, 178, 179, 212, 213, 214, 215, 248, 249, 250, 251]
        
        if y in yBorders:
#            print "y within a  Border!"
            bBorderValueSelected = True
#        else:
#            print "Not yborder, y: ", y, " range: ", yBorders
        return bBorderValueSelected
             
    def adjustCoordByBorders(self, x, y):
        """ Subtract the width of the border(s) from x/y values where applicable """
        (x_offset, y_offset) = (0, 0)
        if (127 < x < (255+4)):
            x_offset -= 4
        
        if (31 < y < (63+4*1)):
            y_offset -= 4
        elif ( (63+4*1) < y < (95+4*2) ):
            y_offset -= 4*2
        elif ( (95+4*2) < y < (127+4*3) ):
            y_offset -= 4*3
        elif ( (127+4*3) < y < (159+4*4) ):
            y_offset -= 4*4
        elif ( (159+4*4) < y < (191+4*5) ):
            y_offset -= 4*5
        elif ( (191+4*5) < y < (223+4*6) ):
            y_offset -= 4*6
        elif ( (223+4*6) < y < (255+4*7) ):
            y_offset -= 4*7
        return x_offset, y_offset
            
if __name__ == '__main__':

    imagePlot()
        