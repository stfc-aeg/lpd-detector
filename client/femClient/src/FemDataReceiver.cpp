/*
 * FemDataReceiver.cpp
 *
 *  Created on: 7 Dec 2011
 *      Author: tcn
 */

#include "FemDataReceiver.h"

FemDataReceiver::FemDataReceiver()
	: mRecvSocket(mIoService, boost::asio::ip::udp::endpoint(boost::asio::ip::udp::v4(), 9000)),
	  mDeadline(mIoService),
	  mAcquiring(false),
	  mCurrentFrame(0),
	  mNumFrames(0)
{
}

FemDataReceiver::~FemDataReceiver()
{

	// Make sure the IO service is stopped and the receiver thread terminated before destroying this object
	this->stopAcquisition();

}

void FemDataReceiver::startAcquisition(void)
{

	if (!mAcquiring) {

		std::cout << "Starting acquisition loop for " << mNumFrames <<  " frames" << std::endl;

		// Set acquisition flag
		mAcquiring = true;

		// Initialise current frame counter to number of frames to be acquired
		mCurrentFrame = mNumFrames;


		if (mCallbacks.allocate)
		{

			// Pre-allocate an initial buffer via the callback
			BufferInfo buffer = mCallbacks.allocate();

			// Launch a thread to start the io_service for receiving data
			mReceiverThread = boost::shared_ptr<boost::thread>(new boost::thread(
					boost::bind(&boost::asio::io_service::run, &mIoService)));
#ifdef SIMULATED_RX
			// Temp - setup deadline timer to simulate data arriving
			mDeadline.expires_from_now(boost::posix_time::milliseconds(mAcquisitionPeriod));

			// Start the deadline actor
			checkDeadline(buffer);
#else

			// Launch async receive on UDP socket
			mRecvSocket.async_receive_from(boost::asio::buffer(buffer.addr, buffer.length), mRemoteEndpoint,
					boost::bind(&FemDataReceiver::handleReceive, this,
							    boost::asio::placeholders::error,
							    boost::asio::placeholders::bytes_transferred
							    )
			);
#endif

		}
		else
		{
			std::cout << "Callbacks not initialised, cannot start receiver" << std::endl;
		}
	}

}

void FemDataReceiver::stopAcquisition(void)
{

	// Set acq flag to false
	mAcquiring = false;

	// Stop the IO service and wait for the receive thread to terminate.
	mIoService.stop();
	if (mReceiverThread)
	{
		mReceiverThread->join();
	}

	// Delete the receiver thread so a new one can be created next time
	mReceiverThread.reset();

}

void FemDataReceiver::setNumFrames(unsigned int aNumFrames)
{
	mNumFrames = aNumFrames;
}

void FemDataReceiver::setAcquisitionPeriod(unsigned int aPeriodMs)
{
	mAcquisitionPeriod = aPeriodMs;
}

void FemDataReceiver::setAcquisitionTime(unsigned int aTimeMs)
{
	mAcquisitionTime = aTimeMs;
}


void FemDataReceiver::registerCallbacks(CallbackBundle* aBundle)
{
	mCallbacks = *aBundle;
}

void FemDataReceiver::checkDeadline(BufferInfo aBuffer)
{
	BufferInfo buffer = aBuffer;

	if (mDeadline.expires_at() <= boost::asio::deadline_timer::traits_type::now())
	{
		// Flag current buffer as received
		if (mCallbacks.receive)
		{
			mCallbacks.receive(mCurrentFrame);
		}

		if (mCurrentFrame == 1)
		{
			// On last frame, stop acq loop and signal completion
			mAcquiring = false;
			mCallbacks.signal(FemDataReceiverSignal::femAcquisitionComplete);
		}
		else if (mCurrentFrame == 0)
		{
			// Do nothing, running continuously
		}
		else
		{

			// Allocate a new buffer
			if (mCallbacks.allocate)
			{
				buffer = mCallbacks.allocate();
				std::cout << "Frame ptr: 0x" << std::hex << (unsigned long)buffer.addr << std::dec << std::endl;
			}

			// Reset deadline timer
			mDeadline.expires_from_now(boost::posix_time::milliseconds(mAcquisitionPeriod));

			// Decrement current frame counter
			mCurrentFrame--;
		}

	}
	if (mAcquiring)
	{
		mDeadline.async_wait(boost::bind(&FemDataReceiver::checkDeadline, this, buffer));
	}
}

void FemDataReceiver::handleReceive(const boost::system::error_code& errorCode, std::size_t bytesReceived)
{

	BufferInfo buffer;

	if (!errorCode && bytesReceived > 0)
	{

		// Flag current buffer as received
		if (mCallbacks.receive)
		{
			mCallbacks.receive(mCurrentFrame);
		}

		if (mCurrentFrame == 1)
		{
			// On last frame, stop acq loop and signal completion
			mAcquiring = false;
			mCallbacks.signal(FemDataReceiverSignal::femAcquisitionComplete);
		}
		else if (mCurrentFrame == 0)
		{
			// Do nothing, running continuously
		}
		else
		{
			// Allocate new buffer
			if (mCallbacks.allocate)
			{
				buffer = mCallbacks.allocate();
			}

			// Decrement frame counter
			mCurrentFrame--;
		}
	}
	else
	{
		std::cout << "Got error during receive: " << errorCode.value() << " : " << errorCode.message() << " recvd=" << bytesReceived << std::endl;
	}

	if (mAcquiring)
	{
		mRecvSocket.async_receive_from(boost::asio::buffer(buffer.addr, buffer.length), mRemoteEndpoint,
				boost::bind(&FemDataReceiver::handleReceive, this,
						    boost::asio::placeholders::error,
						    boost::asio::placeholders::bytes_transferred
						    )
		);
	}

}
