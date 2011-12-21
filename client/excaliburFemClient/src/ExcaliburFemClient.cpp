/*
 * ExcaliburFemClient.cpp
 *
 *  Created on: 7 Dec 2011
 *      Author: tcn
 */

#include "ExcaliburFemClient.h"

ExcaliburFemClient::ExcaliburFemClient(void* aCtlHandle, const CtlCallbacks* aCallbacks,
		const CtlConfig* aConfig, unsigned int aTimeoutInMsecs) :
	FemClient(aConfig->femAddress, aConfig->femPort, aTimeoutInMsecs),
	mCtlHandle(aCtlHandle),
	mCallbacks(aCallbacks),
	mConfig(aConfig)
{

	// Register callbacks for data receiver
	CallbackBundle callbacks;
	callbacks.allocate = boost::bind(&ExcaliburFemClient::allocateCallback, this);
	callbacks.free     = boost::bind(&ExcaliburFemClient::freeCallback, this, _1);
	callbacks.receive  = boost::bind(&ExcaliburFemClient::receiveCallback, this, _1);
	callbacks.signal   = boost::bind(&ExcaliburFemClient::signalCallback, this, _1);

	mFemDataReceiver.registerCallbacks(&callbacks);

}

ExcaliburFemClient::~ExcaliburFemClient() {

}

BufferInfo ExcaliburFemClient::allocateCallback(void)
{

	BufferInfo buffer;

	CtlFrame* frame = mCallbacks->ctlAllocate(mCtlHandle);
	mFrameQueue.push_back(frame);

	buffer.addr    = (u8*)(frame->buffer);
	buffer.length = (frame->bufferLength);

	return buffer;

}


void ExcaliburFemClient::freeCallback(int aVal)
{

	mCallbacks->ctlFree(mCtlHandle, 0);

}


void ExcaliburFemClient::receiveCallback(int aVal)
{

	CtlFrame* frame = mFrameQueue.front();
	mCallbacks->ctlReceive(mCtlHandle,frame);
	mFrameQueue.pop_front();

}


void ExcaliburFemClient::signalCallback(int aSignal)
{

	int theSignal;

	switch (aSignal)
	{
	case FemDataReceiverSignal::femAcquisitionComplete:
		theSignal = FEM_OP_ACQUISITIONCOMPLETE;
		break;

	default:
		theSignal = aSignal;
		break;
	}

	mCallbacks->ctlSignal(mCtlHandle, theSignal);

}

void ExcaliburFemClient::command(unsigned int aCommand)
{

	unsigned int theCommand = 0;
	switch (aCommand)
	{
	case FEM_OP_STARTACQUISITION:
		theCommand = aCommand;
		mFemDataReceiver.startAcquisition();
		break;

	case FEM_OP_STOPACQUISITION:
		theCommand = aCommand;
		mFemDataReceiver.stopAcquisition();
		break;

	default:
		theCommand = aCommand;
		break;
	}

	FemClient::command(theCommand);
}

void ExcaliburFemClient::setNumFrames(unsigned int aNumFrames)
{

	// Set up the number of frames for the receiver thread
	mFemDataReceiver.setNumFrames(aNumFrames);

	// TODO - add FEM write transaction to set this in FEM too
}

void ExcaliburFemClient::setAcquisitionPeriod(unsigned int aPeriodMs)
{

	// Set up the acquisition period for the receiver thread
	mFemDataReceiver.setAcquisitionPeriod(aPeriodMs);

	// TODO - add FEM write transaction to set this in FEM too
}

void ExcaliburFemClient::setAcquisitionTime(unsigned int aTimeMs)
{

	// Set up the acquisition period for the receiver thread
	mFemDataReceiver.setAcquisitionTime(aTimeMs);

	// TODO - add FEM write transaction to set this in FEM too

}
