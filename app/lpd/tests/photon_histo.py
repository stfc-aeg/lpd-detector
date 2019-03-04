import h5py
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colorbar
#from scipy.optimize import curve_fit

fileStub = '/data/lpd/September14/lpdData-0'

startX = 0
endX   = 32
startY = 128
endY   = 128+128
numX = endX - startX
numY = endY - startY


numImagesPerTrain = 10

darkFile = 1202
#darkFile2 = 1693

# Load dark image file
darkNumTrains = 1000
#darkStart = 20
darkData = np.zeros(((darkNumTrains-1)*numImagesPerTrain,numX,numY))
darkFile = h5py.File(fileStub + str(darkFile) + '.hdf5', 'r')
darkData[:] = (darkFile['/lpd/data/image'][numImagesPerTrain:,startX:endX, startY:endY] & 0xFFF)
resultArray = np.zeros((numImagesPerTrain, numX, numY))

#darkData2 = np.zeros(((darkNumTrains-1)*numImagesPerTrain,numX,numY))
#darkFile2 = h5py.File(fileStub + str(darkFile2) + '.hdf5', 'r')
#darkData2[:] = 4096 - (darkFile['/lpd/data/image'][numImagesPerTrain:,startX:endX, startY:endY] & 0xFFF)
#darkMean2 = np.zeros((numImagesPerTrain, numX, numY))
#darkMegaMean = np.zeros((numImagesPerTrain, numX, numY))

for trig in range(numImagesPerTrain):
    resultArray[trig,::] = np.mean(darkData[trig::numImagesPerTrain,::],0)

##for trig in range(numImagesPerTrain):
##    darkMean2[trig,::] = np.mean(darkData2[trig::numImagesPerTrain,::],0)
#
##for trig in range(numImagesPerTrain):
##    darkMegaMean[trig,::] = (darkMean[trig,::] + darkMean2[trig,::])/2
#
#print '...Dark Files Processed'
#
#fileName = fileStub + str(expFile) + '.hdf5'
#
#expNumTrains = 1000
#expNumImages = (expNumTrains-1)*numImagesPerTrain
#expOffsetMean1 = np.zeros(expNumImages)
#expOffsetMean2 = np.zeros(expNumImages)
#expOffsetMean3 = np.zeros(expNumImages)
#
#expData = np.zeros(((expNumTrains-1)*numImagesPerTrain,numX,numY))
#expMean = np.zeros((numImagesPerTrain, numX, numY))
#expSubPed = np.zeros((expNumImages, numX, numY))
#expCMfix = np.zeros((expNumImages, numX, numY))
#expMeanCMfix = np.zeros((1, numX, numY))
#expHybFrames = np.zeros((expNumTrains-1, numX, numY))
#expMeanHybFrame = np.zeros((1, numX, numY))
#
#expFile = h5py.File(fileName, 'r')
#expData[:] = 4096 - (expFile['/lpd/data/image'][numImagesPerTrain:,startX:endX, startY:endY] & 0xFFF)
#
##Pedestal subtraction
#for trig in range(numImagesPerTrain):
#   # expSubPed[trig*(expNumTrains-1):trig*(expNumTrains-1)+(expNumTrains-1),::] =  expData[trig::numImagesPerTrain,::] - darkMean[trig,::]
#    expSubPed[trig::numImagesPerTrain,::] =  expData[trig::numImagesPerTrain,::] - darkMean[trig,::]
#
##CM sample ROI, full tile width in Y, ROI in X
#CMroiXstart = 100
#CMroiXend = 128
#
##CM offsets for each tile and each image
#for n in range(expNumImages):
#  expOffsetMean1[n] = np.mean(expSubPed[n,0:32,CMroiXstart:CMroiXend].flatten())
#  expOffsetMean2[n] = np.mean(expSubPed[n,32:64,CMroiXstart:CMroiXend].flatten())
#  expOffsetMean3[n] = np.mean(expSubPed[n,64:96,CMroiXstart:CMroiXend].flatten())
#
##CM value subtracted from each exp frame
#for n in range(expNumImages):
#  expCMfix[n,0:32,0:128]= expSubPed[n,0:32,0:128] - expOffsetMean1[n]
#  expCMfix[n,32:64,0:128]= expSubPed[n,32:64,0:128] - expOffsetMean2[n]
#  expCMfix[n,64:96,0:128]= expSubPed[n,64:96,0:128] - expOffsetMean3[n]
#
#expMeanCMfix[:]=np.mean(expCMfix[:,::],0) 
#
##Photon Data for frame chosen
#HybFrame = 6
#for train in range(expNumTrains-1):
#    expHybFrames[train,::] = expCMfix[((train*numImagesPerTrain)+HybFrame),::]
#
#expMeanHybFrame[:]=np.mean(expHybFrames[:,::],0) 
#
##Beam ROI Data (For side on beam: 75,122,3,13) (topmiddle: 59,70,0,5)
#BeamRoiXstart = 59
#BeamRoiXend = 70
#BeamRoiYstart = 0
#BeamRoiYend = 5
#
#def gausFunc(x,a,b,c,d,e,f,g,h):
#    return a*np.exp(-((x-b)**2)/(2*c**2))+e*np.exp(-((x-(b+d))**2)/(2*c**2))+f*np.exp(-((x-(b+2*d))**2)/(2*c**2))+g*np.exp(-((x-(b+3*d))**2)/(2*c**2))+h*np.exp(-((x-(b+4*d))**2)/(2*c**2))
#
#hist, bin_edges = np.histogram(expHybFrames[:,BeamRoiYstart:BeamRoiYend,BeamRoiXstart:BeamRoiXend].flatten(), bins=250, range=[-50,200])
#bin_centres = (bin_edges[:-1] + bin_edges[1:])/2
#
##Curve_fit function with initial guess at values a=zero peak, b=zero centre, c=noise, d=spacing, e=one photon peak ...)
##
#
#popt, pcov = curve_fit(gausFunc, bin_centres, hist, p0=[700.0, 0.0, 11.0, 35.0, 700.0, 350.0, 150.0, 50.0] )
#hist_fit = gausFunc(bin_centres, *popt)
#
#print 'Zero Peak Height =', popt[0]
#print 'Zero centre =', popt[1]
#print 'Noise =', popt[2]
#print 'Peak Spacing =', popt[3]
#print 'One Photon Height =', popt[4]
#print 'Two Photon Height =', popt[5]
#print 'Three Photon Height =', popt[6]
#
#ax = plt.subplot2grid((3,3),(0,0))
#img1 = ax.imshow(expMeanCMfix[0,::], interpolation='nearest', vmin=-10, vmax=200)
#plt.title('Overview: mean of all images')
#axc, kw = matplotlib.colorbar.make_axes(ax)
#cb = matplotlib.colorbar.Colorbar(axc, img1)
#
#ax2 = plt.subplot2grid((3,3),(0,1), colspan=2)
#img2 = ax2.imshow(expMeanHybFrame[0,BeamRoiYstart:BeamRoiYend,BeamRoiXstart:BeamRoiXend], interpolation='nearest', vmin=-5, vmax=100)
#plt.title('ROI: mean of Hybrid images')
#axc, kw = matplotlib.colorbar.make_axes(ax2)
#cb = matplotlib.colorbar.Colorbar(axc, img2)
#
#plt.subplot2grid((3,3),(1,0), colspan=3, rowspan=2)
#plt.hist(expHybFrames[:,BeamRoiYstart:BeamRoiYend,BeamRoiXstart:BeamRoiXend].flatten(), bins=250, range=[-50,200], facecolor='green', alpha=0.5)
#plt.plot(bin_centres, hist_fit, 'r--')
#plt.xlabel('Noise in ADC Codes')
#plt.ylabel('Freq')
#plt.title('ROI Histogram of pixel values')
#
#
#plt.show()
#
