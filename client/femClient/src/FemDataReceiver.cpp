/*
 * FemDataReceiver.cpp
 *
 *  Created on: 7 Dec 2011
 *      Author: tcn
 */

#include "FemDataReceiver.h"

FemDataReceiver::FemDataReceiver()
	: mDeadline(mIoService),
	  mReceiverThread(new boost::thread(boost::bind(&boost::asio::io_service::run, &mIoService))),
	  mCallbackCount(0)
{

	// Temp - setup deadline timer
	mDeadline.expires_from_now(boost::posix_time::seconds(1));

	// Explicitly clear callback
	mReceiveCallback = 0;

	// Start the deadline actor
	checkDeadline();
}

FemDataReceiver::~FemDataReceiver() {

	// Stop the IO service and wait for the receive thread to terminate. This needs to
	// happen before the destructor completes and the IO service gets destroyed
	mIoService.stop();
	mReceiverThread->join();

}

void FemDataReceiver::start(void)
{
	// Launch a thread to start the io_service for receiving data
//	mReceiverThread = new boost::thread(
//			boost::bind(&boost::asio::io_service::run, &mIoService));

}

void FemDataReceiver::registerAllocateCallback(allocateCallback_t aCallback)
{
	mAllocateCallback = aCallback;
}


void FemDataReceiver::registerFreeCallback(freeCallback_t aCallback)
{
	mFreeCallback = aCallback;
}


void FemDataReceiver::registerReceiveCallback(receiveCallback_t aCallback)
{
	mReceiveCallback = aCallback;
}

void FemDataReceiver::registerSignalCallback(signalCallback_t aCallback)
{
	mSignalCallback = aCallback;
}


void FemDataReceiver::checkDeadline(void)
{
	if (mDeadline.expires_at() <= boost::asio::deadline_timer::traits_type::now())
	{
		std::cout << "Deadline expired!" << std::endl;
		if (mReceiveCallback)
		{
			mReceiveCallback(mCallbackCount++);
		}
		mDeadline.expires_from_now(boost::posix_time::seconds(1));
	}
	mDeadline.async_wait(boost::bind(&FemDataReceiver::checkDeadline, this));
}

void FemDataReceiver::completionCallback(void)
{
	std::cout << "In completion callback function" << std::endl;
}
