from matplotlib import cbook
import matplotlib.pyplot as plt
import matplotlib.text as text

import argparse
import numpy as np
import h5py
import matplotlib
import sys, time
from LpdReadoutConfig import *


def imagePlot():

    args = parseArgs()

    with h5py.File(args.fileName, 'r') as hdfFile:

        # Read in the train, image counter and timestamp arrays
        trainNumber = hdfFile['/lpd/data/trainNumber'][...]
        imageNumber = hdfFile['/lpd/data/imageNumber'][...]
        timeStamp   = hdfFile['/lpd/data/timeStamp'][...]

        # Get max train and image number form arrays
        maxTrainNumber = np.amax(trainNumber)
        maxImageNumber = np.amax(imageNumber)

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
        if numTrains != maxTrainNumber + 1:
            print "WARNING: mismatch in number of trains between metadata and file"

        if args.train > maxTrainNumber:
            print "ERROR: train number specified (%d) is bigger than maximum in data (%d), quitting" \
                % (args.train, maxTrainNumber)
            sys.exit(1)

        # Check image number requested in argument is in range too
        if args.image > maxImageNumber:
            print "ERROR: images number specified (%d) is bigger than maximum in data (%d), quitting" \
            % (args.image, maxImageNumber)
            sys.exit(1)

        # Calculate image offset into array and range check (should be OK)
        imgOffset = (args.train * (maxImageNumber + 1)) + args.image
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
        
#        print "image =.. took: ", t2 - t1
#        print "imageData = image.. took: ", t3 - t2

        # Mask off or select gain range from image data
        if args.gain == 0:
            imageData[:] = imageData[:] & 0xFFF

        # Invert image if specified
        if args.invert != None:
            imageData[:] = 4096 - imageData[:]

        dateStr = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(timeStamp[imgOffset]))
        titleText = 'Run %d Train %d Image %d : %s' \
            % (meta.attrs['runNumber'], trainNumber[imgOffset], imageNumber[imgOffset],
            dateStr)
        
        # Plot the figure
        fig = plt.figure(1)
        ax = fig.add_subplot(111)
        img = ax.imshow(imageData, interpolation='nearest', vmin='0', vmax='4095')
        plt.title(titleText)

        # Add a colour bar
        axc, kw = matplotlib.colorbar.make_axes(ax)
        cb = matplotlib.colorbar.Colorbar(axc, img)    
        img.colorbar = cb

        # Obtain artist from figure - needed by DataCursor class        
        children = fig.get_children()
        DataCursor(children[1], imageData)
        plt.show()


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

    args = parser.parse_args()

    return args

# -------           Copied example from stack overflow:                --------- #

class DataCursor(object):
    ''' Modified from example at: http://stackoverflow.com/a/13306887/2903608 '''
    """A simple data cursor widget that displays the x,y location of a
    matplotlib artist when it is selected."""
    def __init__(self, artists, imageData, tolerance=5, offsets=(-20, 20), 
                 #template='x: %0.2f\ny: %0.2f\nPxl: %i',
                 template='Column: %i\nRow: %i\nPixel: %i', display_all=False):
        """Create the data cursor and connect it to the relevant figure.
        "artists" is the matplotlib artist or sequence of artists that will be 
            selected. 
        "imageData" is LPD image data for a super module.
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
            annotation.set_text(self.template % (x, y, self.imageData[y, x]))
            annotation.set_visible(True)
            event.canvas.draw()

if __name__ == '__main__':

    imagePlot()
        