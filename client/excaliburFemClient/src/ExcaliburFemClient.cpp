/*
 * ExcaliburFemClient.cpp - EXCALIBUR FEM client class implementation
 *
 *  Created on: 7 Dec 2011
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "ExcaliburFemClient.h"
#include "ExcaliburFrontEndDevices.h"
#include "asicControlParameters.h"
#include "mpx3Parameters.h"
#include "time.h"
#include <map>
#include <iostream>
#include <iomanip>
#include <sstream>

typedef void (ExcaliburFemClient::*ExcaliburScanFunc)(void);

ExcaliburFemClient::ExcaliburFemClient(void* aCtlHandle, const CtlCallbacks* aCallbacks,
		const CtlConfig* aConfig, unsigned int aTimeoutInMsecs) :
	FemClient(aConfig->femAddress, aConfig->femPort, aTimeoutInMsecs),
	mMpx3GlobalTestPulseEnable(false),
	mMpx3TestPulseCount(4000),
	mFemDataHostPort(kHostDataPort),
	mCtlHandle(aCtlHandle),
	mCallbacks(aCallbacks),
	mConfig(aConfig),
	mAsicDataReorderMode(reorderedDataMode),
	mNumSubFrames(2),
	mBurstModeSubmitPeriod(0),
	mEnableDeferredBufferRelease(false),
	mDacScanDac(0),
	mDacScanStart(0),
	mDacScanStop(0),
	mDacScanStep(0)
{

	// Initialize MPX3 DAC settings, values and pixel config caches to zero
	for (unsigned int iChip = 0; iChip < kNumAsicsPerFem; iChip++)
	{
		for (unsigned int iDac = 0; iDac < numExcaliburDacs; iDac++)
		{
			mMpx3DacCache[iChip][iDac] = 0;
		}

		for (unsigned int iConfig= 0; iConfig < numPixelConfigs; iConfig++) {
			for (unsigned int iPixel = 0; iPixel < kNumPixelsPerAsic; iPixel++)
			{
				mMpx3PixelConfigCache[iChip][iConfig][iPixel]       = 0;
			}
		}

		// Initialise default values for some standard parameters used in all
		// OMR transactions
		mMpx3OmrParams[iChip].readWriteMode         = sequentialReadWriteMode;
//		mMpx3OmrParams[iChip].polarity              = electronPolarity;
		mMpx3OmrParams[iChip].polarity              = holePolarity;
		mMpx3OmrParams[iChip].readoutWidth          = readoutWidth8;
		mMpx3OmrParams[iChip].unusedPTEnable        = 0;
		mMpx3OmrParams[iChip].testPulseEnable       = 0;
		mMpx3OmrParams[iChip].counterDepth          = counterDepth12;
		mMpx3OmrParams[iChip].columnBlock           = 0;
		mMpx3OmrParams[iChip].columnBlockSelect     = 0;
		mMpx3OmrParams[iChip].rowBlock              = 0;
		mMpx3OmrParams[iChip].rowBlockSelect        = 0;
		mMpx3OmrParams[iChip].equalizeTHH           = 0;
		mMpx3OmrParams[iChip].colourMode            = monochromeMode;
		mMpx3OmrParams[iChip].pixelComEnable        = 0;
		mMpx3OmrParams[iChip].shutterCtr            = 0;
		mMpx3OmrParams[iChip].fuseSel               = 0;
		mMpx3OmrParams[iChip].fusePulseWidth        = 0;
		mMpx3OmrParams[iChip].dacSense              = 0;
		mMpx3OmrParams[iChip].dacExternal           = 0;
		mMpx3OmrParams[iChip].externalBandGapSelect = 0;

		// Initialise chip column test pulse enables
		for (unsigned int iCol = 0; iCol < kNumColsPerAsic; iCol++)
		{
			mMpx3ColumnTestPulseEnable[iChip][iCol] = 0;
		}

		// Initialise chip enable flag
		mMpx3Enable[iChip] = true;

	}

	// Reset the ASIC control f/w block and ASICS
//	this->asicControlReset();
//	this->asicControlAsicReset();

	// Initialise front-end DACs
	//this->frontEndDacInitialise();

	// Build callback bundle to be registered with the data receiver
	mCallbackBundle.allocate = boost::bind(&ExcaliburFemClient::allocateCallback, this);
	mCallbackBundle.free     = boost::bind(&ExcaliburFemClient::freeCallback, this, _1);
	mCallbackBundle.receive  = boost::bind(&ExcaliburFemClient::receiveCallback, this, _1, _2);
	mCallbackBundle.signal   = boost::bind(&ExcaliburFemClient::signalCallback, this, _1);

	// Initialise 10GigE UDP firmware block
	// TODO some of these parameters need to be passed in config block and/or derived
	u32 hostPort = kHostDataPort;
	u32 fpgaPort = 8;
	char* fpgaIPAddress = "10.0.2.2";
	char* fpgaMacAddress = "62:00:00:00:00:01";
	char* hostIpAddress = "10.0.2.1";

	u32 rc = this->configUDP(fpgaMacAddress, fpgaIPAddress, fpgaPort, hostIpAddress, hostPort);
	if (rc != 0)
	{
		throw FemClientException((FemClientErrorCode)excaliburFemClientUdpSetupFailed, "Failed to set up FEM UDP firmware block");
	}

	try
	{
		mFemDataReceiver = new FemDataReceiver(mFemDataHostPort);
	}
	catch (boost::system::system_error &e)
	{
		std::ostringstream msg;
		msg << "Failed to create FEM data receiver: " << e.what();
		throw FemClientException((FemClientErrorCode)excaliburFemClientDataReceviverSetupFailed, msg.str());
	}

	// Check DMA engine acquisition state and reset to IDLE if in a different state
	FemAcquireStatus acqStatus = this->acquireStatus();
	if (acqStatus.state != acquireIdle)
	{
		std::cout << "Acquisition state at startup is " << acqStatus.state << " sending stop to reset" << std::endl;
		this->acquireStop();
	}
	else
	{
		std::cout << "Acquisition state is IDLE at startup" << std::endl;
	}
}


ExcaliburFemClient::~ExcaliburFemClient() {

	// Delete the data receiver object if it was created
	if (mFemDataReceiver)
	{
		delete (mFemDataReceiver);
	}

}

BufferInfo ExcaliburFemClient::allocateCallback(void)
{

	BufferInfo buffer;
	CtlFrame* frame;

	// If the frame queue is empty (i.e. no pre-allocated frame buffers), request
	// a frame via the callback, otherwise use the front-most frame in the queue

	if (mFrameQueue.empty())
	{
		frame = mCallbacks->ctlAllocate(mCtlHandle);
		mFrameQueue.push_back(frame);
	}
	else
	{
		frame = mFrameQueue.front();
	}

	// Map the frame information into the buffer to return
	buffer.addr    = (u8*)(frame->buffer);
	buffer.length = (frame->bufferLength);

	return buffer;

}


void ExcaliburFemClient::freeCallback(int aVal)
{

	mCallbacks->ctlFree(mCtlHandle, 0);

}


void ExcaliburFemClient::receiveCallback(int aFrameCounter, time_t aRecvTime)
{

	// Get the first frame on our queue
	CtlFrame* frame = mFrameQueue.front();

	// Fill fields into frame metadata
	frame->frameCounter = aFrameCounter;
	frame->timeStamp    = aRecvTime;

	// If deferred buffer release is enabled, queue the completed
	// frame on the release queue, otherwise call the receive callback
	// to release the frame
	if (mEnableDeferredBufferRelease)
	{
		mReleaseQueue.push_back(frame);
	}
	else
	{
		mCallbacks->ctlReceive(mCtlHandle,frame);
	}

	// Pop the frame off the queue
	mFrameQueue.pop_front();

}


void ExcaliburFemClient::signalCallback(int aSignal)
{

	int theSignal;

	switch (aSignal)
	{

	case FemDataReceiverSignal::femAcquisitionComplete:

		theSignal = FEM_OP_ACQUISITIONCOMPLETE;
		std::cout << "Got acquisition complete signal" << std::endl;
		//this->acquireStop();
		//this->stopAcquisition();

		// If deferred buffer release is enabled, drain the release queue
		// out through the receive callback at the requested rate
		if (mEnableDeferredBufferRelease)
		{
			this->releaseAllFrames();
		}
		break;

	case FemDataReceiverSignal::femAcquisitionCorruptImage:
		theSignal = FEM_OP_CORRUPTIMAGE;
		std::cout << "Got corrupt image signal" << std::endl;
		break;

	default:
		theSignal = aSignal;
		break;

	}

	mCallbacks->ctlSignal(mCtlHandle, theSignal);

}

void ExcaliburFemClient::preallocateFrames(unsigned int aNumFrames)
{
	for (unsigned int i = 0; i < aNumFrames; i++)
	{
		CtlFrame* frame = mCallbacks->ctlAllocate(mCtlHandle);
		if (frame != NULL)
		{
			mFrameQueue.push_back(frame);
		}
		else
		{
			throw FemClientException((FemClientErrorCode)excaliburFemClientBufferAllocateFailed, "Buffer allocation callback failed");
		}
	}
	std::cout << "Preallocate complete - frame queue size is now " << mFrameQueue.size() << std::endl;
}

void ExcaliburFemClient::releaseAllFrames(void)
{
	int numFramesToRelease = mReleaseQueue.size();
	std::cout << "Deferred buffer release - draining release queue of "
			  << numFramesToRelease << " frames" << std::endl;

	// Build a timespec for the release period
	time_t releaseSecs = (time_t)((int)mBurstModeSubmitPeriod);
	long   releaseNsecs = (long)((mBurstModeSubmitPeriod - releaseSecs)*1E9);
	struct timespec releasePeriod = {releaseSecs, releaseNsecs};

	struct timespec startTime, endTime;
	clock_gettime(CLOCK_REALTIME, &startTime);

	while (mReleaseQueue.size() > 0)
	{
		CtlFrame* frame = mReleaseQueue.front();
		mCallbacks->ctlReceive(mCtlHandle, frame);
		mReleaseQueue.pop_front();
		if (mBurstModeSubmitPeriod > 0.0)
		{
			nanosleep((const struct timespec *)&releasePeriod, NULL);
		}
	}

	clock_gettime(CLOCK_REALTIME, &endTime);
	double startSecs = startTime.tv_sec  + ((double)startTime.tv_nsec / 1.0E9);
	double endSecs   = endTime.tv_sec  + ((double)endTime.tv_nsec / 1.0E9);
	double elapsedSecs = endSecs - startSecs;
	double elapsedRate = (double)numFramesToRelease / elapsedSecs;

	std::cout << "Release completed: " << numFramesToRelease << " frames released in "
			  << elapsedSecs << " secs, rate: " << elapsedRate << " Hz"
			  << std::endl;

}

void ExcaliburFemClient::freeAllFrames(void)
{

	while (mFrameQueue.size() > 0)
	{
		CtlFrame* frame = mFrameQueue.front();
		mCallbacks->ctlFree(mCtlHandle, frame);
		mFrameQueue.pop_front();
	}

}
void ExcaliburFemClient::command(unsigned int aCommand)
{

	unsigned int theCommand = 0;
	switch (aCommand)
	{
	case FEM_OP_STARTACQUISITION:
		this->startAcquisition();
		//this->toyAcquisition();
		break;

	case FEM_OP_STOPACQUISITION:
		this->stopAcquisition();
		break;

	default:
		theCommand = aCommand;
		FemClient::command(theCommand);
		break;
	}


}

void ExcaliburFemClient::toyAcquisition(void)
{
	std::cout << "Running toy acquisition loop for numFrames=" << mNumFrames << std::endl;
	for (unsigned int iBuffer = 0; iBuffer < mNumFrames; iBuffer++)
	{
		BufferInfo aBuffer = this->allocateCallback();
		this->receiveCallback(iBuffer, (time_t)1234);
	}
	this->signalCallback(FemDataReceiverSignal::femAcquisitionComplete);
	std::cout << "Ending toy acq loop" << std::endl;

}


void ExcaliburFemClient::startAcquisition(void)
{

	struct timespec startTime, endTime;

	clock_gettime(CLOCK_REALTIME, &startTime);

	// Default values for various acquisition parameters
	u32 acqMode, numAcq, bdCoalesce = 0;
	unsigned int numRxFrames = mNumFrames; // Default data receiver to receive specified number of frames
	bool bufferPreAllocate = false;
	bool clientAcquisitionControl = true;
	bool enableFrameCounterCheck = true;
	ExcaliburScanFunc theScanFunc = NULL;

	// Select various parameters based on operation mode
	switch (mOperationMode)
	{

	case excaliburOperationModeNormal:
		acqMode = ACQ_MODE_NORMAL;
		numAcq = 0; // Let the acquire config command configure all buffers in this mode
		bdCoalesce = 1;
		mEnableDeferredBufferRelease = false;
		break;

	case excaliburOperationModeBurst:
		acqMode = ACQ_MODE_BURST;
		numAcq = mNumFrames;
		bdCoalesce = 1;
		mEnableDeferredBufferRelease = true;
		bufferPreAllocate = true;
		break;

	case excaliburOperationModeDacScan:
		acqMode = ACQ_MODE_NORMAL;
		numAcq = 0;
		bdCoalesce = 1;
		mEnableDeferredBufferRelease = false;
		enableFrameCounterCheck = false;
		numRxFrames = this->dacScanNumSteps(); // Override number of frames to receive based on number of steps in scan
		clientAcquisitionControl = false;      // FEM will be in control of acquisition sequence for DAC scan
		theScanFunc = &ExcaliburFemClient::dacScanExecute;    // Set scan function pointer to DAC scan execute member function
		break;

	case excaliburOperationModeHistogram:
		// Deliberate fall-thru as histogram mode not yet supported

	default:
		{
			std::ostringstream msg;
			msg << "Cannot start acquisition, illegal operation mode specified: " << mOperationMode;
			throw FemClientException((FemClientErrorCode)excaliburFemClientIllegalOperationMode, msg.str());
		}
		break;
	}

	// Pre-allocate frame buffers for data receiver if necessary
	if (bufferPreAllocate)
	{
		this->preallocateFrames(numRxFrames);
	}

	// Register callbacks for data receiver
	mFemDataReceiver->registerCallbacks(&mCallbackBundle);

	// Set up the number of frames, acquisition period and time for the receiver thread
	mFemDataReceiver->setNumFrames(numRxFrames);
	mFemDataReceiver->setAcquisitionPeriod(mAcquisitionPeriodMs);
	mFemDataReceiver->setAcquisitionTime(mAcquisitionTimeMs);

	// Set up frame length and header sizes for the data receiver thread
	mFemDataReceiver->setFrameHeaderLength(8);
	mFemDataReceiver->setFrameHeaderPosition(headerAtStart);
	mFemDataReceiver->setNumSubFrames(mNumSubFrames);

	unsigned int frameDataLengthBytes = this->frameDataLengthBytes();
	mFemDataReceiver->setFrameLength(frameDataLengthBytes);

	mFemDataReceiver->enableFrameCounterCheck(enableFrameCounterCheck);

	// Start the data receiver thread
	mFemDataReceiver->startAcquisition();

	// Set up the acquisition DMA controller and arm it, based on operation mode
	unsigned int dmaSize = this->asicReadoutDmaSize();
	this->acquireConfig(acqMode, dmaSize, 0, numAcq, bdCoalesce);
	this->acquireStart();

	// Set up counter depth for ASIC control based on current OMR settings
	this->asicControlCounterDepthSet(mMpx3OmrParams[0].counterDepth);

	// Set ASIC data reordering mode
	this->rdmaWrite(kExcaliburDataReorderMode, mAsicDataReorderMode);

	// Set up the readout length in clock cycles for the ASIC control block
	unsigned int readoutLengthCycles = this->asicReadoutLengthCycles();
	this->asicControlReadoutLengthSet(readoutLengthCycles);

	// If the client is in control of this acquisition mode, set up and start the acquisition
	if (clientAcquisitionControl)
	{

		// Set up the number of frames to be acquired in the ASIC control block
		this->asicControlNumFramesSet(numRxFrames);

		// Set up the acquisition period in the ASIC control block
		// TODO not yet implemented in firmware

		// Set up the acquisition time in the ASIC control block, convering from milliseconds
		// to microseconds
		this->asicControlShutterDurationSet(mAcquisitionTimeMs * 1000);

		// Build chip mask from the enable flags and determine which is the first chip active - this is used
		// to select settings for building the OMR for readout transactions, where the OMR is broadcast
		// to all chips
		int firstChipActive = -1;
		unsigned int chipMask = 0;
		for (unsigned int iChip = 0; iChip < kNumAsicsPerFem; iChip++)
		{
			if (mMpx3Enable[iChip])
			{
				chipMask |= ((unsigned int)1 << (7 - iChip));
				if (firstChipActive == -1)
				{
					firstChipActive = iChip;
				}
			}
		}
		std::cout << "Chip mask: 0x" << std::hex << chipMask << std::dec << " First chip active: " << firstChipActive << std::endl;

		// Set up the ASIC mux based on calculated chip mask
		this->asicControlMuxSet(chipMask);

		// Check if test pulses are enabled on any enabled chip, if so set the global test pulse enable flag
		for (unsigned int iChip = 0; iChip < kNumAsicsPerFem; iChip++)
		{
			if (mMpx3Enable[iChip] && mMpx3OmrParams[iChip].testPulseEnable)
			{
				mMpx3GlobalTestPulseEnable = true;
			}
		}

		if (mMpx3GlobalTestPulseEnable)
		{
			std::cout << "Enabling test pulse injection on FEM (count=" << mMpx3TestPulseCount << ")" << std::endl;
			this->asicControlTestPulseCountSet(mMpx3TestPulseCount);
		}

		// Set up OMR mode and execute command based on which counter is selected
		mpx3OMRMode omrMode = (mpx3OMRMode)0;
		unsigned int executeCmd = 0;
		switch (mMpx3CounterSelect)
		{
		case mpx3Counter0:
			omrMode    = readPixelMatrixC0;
			executeCmd = asicRunSequentialC0;
			break;

		case mpx3Counter1:
			omrMode    = readPixelMatrixC1;
			executeCmd = asicRunSequentialC1;
			break;

		default:
			{
				std::ostringstream msg;
				msg << "Cannot start acquisition, illegal counter select specified: " << mMpx3CounterSelect;
				throw FemClientException((FemClientErrorCode)excaliburFemClientIllegalCounterSelect, msg.str());
			}

			break;
		}

		// Set up the OMR for readout using the first active chip to retrieve
		// default values for OMR fields
		mpx3Omr theOmr = this->mpx3OMRBuild(firstChipActive, omrMode);
		std::cout << "OMR: 0x" << std::hex << theOmr.raw << std::dec << std::endl;
		this->asicControlOmrSet(theOmr);

		// Enable test pulses in the execute command if necessary
		if (mMpx3GlobalTestPulseEnable)
		{
			executeCmd |= asicTestPulseEnable;
		}

		// Enable external trigger in the execute command and set trigger polarity if selected
		if (mExternalTrigger)
		{

			executeCmd |= asicExternalTrigger;
			// TODO Needs API selection for polarity
			this->asicControlConfigRegisterSet(externalTrigActiveHigh);
		}

		// Execute the command
		std::cout << "Sending execute command 0x" << std::hex << executeCmd << std::dec << std::endl;
		this->asicControlCommandExecute((asicControlCommand)executeCmd);

	}
	else
	{
		// Invoke the scan member execute function defined above
		if (theScanFunc != NULL)
		{
			std::cout << "Executing autonomous scan sequence with " << numRxFrames << " steps" << std::endl;
			(this->*(theScanFunc))();
		}
		else
		{
			throw FemClientException((FemClientErrorCode)excaliburFemClientMissingScanFunction, "Missing scan function for this acquisition mode");
		}

	}

	clock_gettime(CLOCK_REALTIME, &endTime);

	double startSecs = startTime.tv_sec  + ((double)startTime.tv_nsec / 1.0E9);
	double endSecs   = endTime.tv_sec  + ((double)endTime.tv_nsec / 1.0E9);
	double elapsedSecs = endSecs - startSecs;

	std::cout << "startAcquisition call took " << elapsedSecs << " secs" << std::endl;
}

void ExcaliburFemClient::stopAcquisition(void)
{

	// Check if acquisition is active in data receiver. If so
	// send stop command to ASIC control block to terminate after
	// current ASIC transfer
	if (mFemDataReceiver != 0)
	{
		if (mFemDataReceiver->acqusitionActive())
		{
			std::cout << "ACQ active, sending stop" << std::endl;
			this->asicControlCommandExecute(asicStopAcquisition);

			usleep(10000);
			u32 ctrlState = this->rdmaRead(kExcaliburAsicCtrlState1);
			std::cout << "ctrlState1=0x" << std::hex << ctrlState << std::dec << std::endl;

		}
	}
	// Send ACQUIRE stop command to the FEM
	// TODO check if stopped already?
	this->acquireStop();

	if (mFemDataReceiver != 0)
	{
		// Ensure that the data receiver has stopped cleanly
		mFemDataReceiver->stopAcquisition();

		// Delete the data receiver
		//delete(mFemDataReceiver);
		//mFemDataReceiver = 0;
	}

	// Reset ASIC control firmware block
	// TODO is this necessary - was put in to reset frame counter
	this->asicControlReset();

}

void ExcaliburFemClient::externalTriggerSet(unsigned int aExternalTrigger)
{
	// Store external trigger setup for use during acquisition start
	mExternalTrigger = aExternalTrigger;
}

void ExcaliburFemClient::operationModeSet(unsigned int aOperationMode)
{
	// Store operation mode for use during acquisition start
	mOperationMode = (excaliburOperationMode)aOperationMode;
}

void ExcaliburFemClient::numFramesSet(unsigned int aNumFrames)
{
	// Store number of frames to be received for use during acquisition start
	mNumFrames = aNumFrames;
}

void ExcaliburFemClient::acquisitionPeriodSet(unsigned int aPeriodMs)
{
	// Store acquisition period for use during acquisition start
	mAcquisitionPeriodMs = aPeriodMs;
}

void ExcaliburFemClient::acquisitionTimeSet(unsigned int aTimeMs)
{
	// Store acquisition time for use during acquisition start
	mAcquisitionTimeMs = aTimeMs;
}

void ExcaliburFemClient::burstModeSubmitPeriodSet(double aPeriod)
{

	// Store burst mode submit period for use during acquisition
	mBurstModeSubmitPeriod = aPeriod;
	std::cout << "Set burst mode submit period to " << aPeriod << std::endl;

}

void ExcaliburFemClient::numTestPulsesSet(unsigned int aNumTestPulses)
{
	// Store number of test pulses for use during acquisition start
	mMpx3TestPulseCount = aNumTestPulses;
}

unsigned int ExcaliburFemClient::asicReadoutDmaSize(void)
{

	// Get counter bit depth of ASIC
	unsigned int counterBitDepth = this->mpx3CounterBitDepth(mMpx3OmrParams[0].counterDepth);

	// DMA size is (numRows * numCols * (numAsics/2) counterDepth /  8 bits per bytes
	unsigned int theLength = (kNumRowsPerAsic * kNumColsPerAsic * (kNumAsicsPerFem / 2) * counterBitDepth) / 8;

	return theLength;
}

unsigned int ExcaliburFemClient::asicReadoutLengthCycles(void)
{

	unsigned int counterBitDepth = this->mpx3CounterBitDepth(mMpx3OmrParams[0].counterDepth);
	unsigned int readoutBitWidth = this->mpx3ReadoutBitWidth(mMpx3OmrParams[0].readoutWidth);

	unsigned int theLength = (kNumRowsPerAsic * kNumColsPerAsic * counterBitDepth) / readoutBitWidth;

	return theLength;

}

unsigned int ExcaliburFemClient::frameDataLengthBytes(void)
{

	unsigned int frameDataLengthBytes = 0;

	// Get the counter bit depth
	unsigned int counterBitDepth = this->mpx3CounterBitDepth(mMpx3OmrParams[0].counterDepth);

	// Calculate raw length of ASIC data in bits
	unsigned int asicDataLengthBits = kNumRowsPerAsic * kNumColsPerAsic * kNumAsicsPerFem * counterBitDepth;

	// Get the frame length in bytes. In 12/24-bit re-ordered mode, reordering expands each 12 bit ASIC
	// counter up to 16 bits (two bytes)
	if (mAsicDataReorderMode == reorderedDataMode)
	{
		switch (mMpx3OmrParams[0].counterDepth)
		{
		case counterDepth1:
		case counterDepth4:
			frameDataLengthBytes = (asicDataLengthBits / 8);
			break;

		case counterDepth12:
		case counterDepth24:
			frameDataLengthBytes = ((asicDataLengthBits * 16)  / 12) / 8;
			break;

		default:
			break;
		}
	}

	// Add on size of frame counter(s), which is 8 bytes per subframe
	//frameDataLengthBytes += (mNumSubFrames * 8);

	return frameDataLengthBytes;

}

void ExcaliburFemClient::frontEndInitialise(void)
{

	std::cout << "**** Front-end initialise ****" << std::endl;
	sleep(3);

	// Initialise front-end DACs
	this->frontEndDacInitialise();

	// Reset the ASIC control f/w block and ASICS
	this->asicControlReset();
	this->asicControlAsicReset();

	std::cout << "**** Front-end init done ****" << std::endl;

}
