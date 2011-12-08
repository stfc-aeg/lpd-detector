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

	// Register callbacsk for data receiver
	mFemDataReceiver.registerAllocateCallback(boost::bind(&ExcaliburFemClient::allocateCallback, this));
	mFemDataReceiver.registerFreeCallback(boost::bind(&ExcaliburFemClient::freeCallback, this, _1));
	mFemDataReceiver.registerReceiveCallback(boost::bind(&ExcaliburFemClient::receiveCallback, this, _1));
	mFemDataReceiver.registerSignalCallback(boost::bind(&ExcaliburFemClient::signalCallback, this, _1));
}

ExcaliburFemClient::~ExcaliburFemClient() {

}

void ExcaliburFemClient::allocateCallback(void)
{

	std::cout << "In ExcaliburFemClient::allocateCallback: " << std::endl;
	CtlFrame* frame = mCallbacks->ctlAllocate(mCtlHandle);

}


void ExcaliburFemClient::freeCallback(int aVal)
{

	std::cout << "In ExcaliburFemClient::freeCallback: " << std::endl;
	mCallbacks->ctlFree(mCtlHandle, 0);

}


void ExcaliburFemClient::receiveCallback(int aVal)
{

	std::cout << "In ExcaliburFemClient::receiveCallback: " << aVal << std::endl;
	mCallbacks->ctlReceive(mCtlHandle,0);

}


void ExcaliburFemClient::signalCallback(int aSignal)
{

	std::cout << "In ExcaliburFemClient::signalCallback: " << aSignal << std::endl;
	mCallbacks->ctlSignal(mCtlHandle, aSignal);

}
