/*
 * FemDataReceiver.cpp
 *
 *  Created on: 7 Dec 2011
 *      Author: tcn
 */

#include "FemClient.h"
#include "FemDataReceiver.h"

FemDataReceiver::FemDataReceiver()
	: mRecvSocket(mIoService, boost::asio::ip::udp::endpoint(boost::asio::ip::udp::v4(), 61649)),
	  mDeadline(mIoService),
	  mAcquiring(false),
	  mCurrentFrame(0),
	  mNumFrames(0),
	  mFrameLength(0),
	  mFrameTotalBytesReceived(0),
	  mFramePayloadBytesReceived(0)
{
	int nativeSocket = (int)mRecvSocket.native_handle();
	int rcvBufSize = 8388608;
	setsockopt(nativeSocket, SOL_SOCKET, SO_RCVBUF, (void*)&rcvBufSize, sizeof(rcvBufSize));
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

		// Initialise bytes received counter for next frame
		mFramePayloadBytesReceived = 0;

		if (mCallbacks.allocate)
		{

			// Pre-allocate an initial buffer via the callback
			mCurrentBuffer = mCallbacks.allocate();

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
			boost::array<boost::asio::mutable_buffer, 2> rxBufs = {{
				boost::asio::buffer((void*)&mPacketHeader, sizeof(mPacketHeader)),
				boost::asio::buffer(mCurrentBuffer.addr, mCurrentBuffer.length) }};

			mRecvSocket.async_receive_from(rxBufs, //boost::asio::buffer(mCurrentBuffer.addr, mCurrentBuffer.length),
					mRemoteEndpoint,
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

void FemDataReceiver::setFrameLength(unsigned int aFrameLength)
{
	mFrameLength = aFrameLength;
	std::cout << "DEBUG frame length = " << mFrameLength << std::endl;
}

void FemDataReceiver::setAcquisitionPeriod(unsigned int aPeriodMs)
{
	mAcquisitionPeriod = aPeriodMs;
}

void FemDataReceiver::setAcquisitionTime(unsigned int aTimeMs)
{
	mAcquisitionTime = aTimeMs;
}

void FemDataReceiver::setFrameHeaderLength(unsigned int aHeaderLength)
{
	mFrameHeaderLength = aHeaderLength;
}

void FemDataReceiver::setFrameHeaderPosition(FemDataReceiverHeaderPosition aPosition)
{
	mHeaderPosition = aPosition;
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

	if (!errorCode && bytesReceived > 0)
	{

		mFrameTotalBytesReceived   += bytesReceived;
		mFramePayloadBytesReceived += (bytesReceived - mFrameHeaderLength);

//		std::cout << std::hex << mPacketHeader.frameNumber << " " << mPacketHeader.packetNumberFlags << std::dec << " "
//				  << bytesReceived << " " << mFrameTotalBytesReceived << " " << mFramePayloadBytesReceived << std::endl;

		// Flag current buffer as received if completed -
		// TODO: this calc will need to be more complex to cope with headers/trailers etc

		if (mFramePayloadBytesReceived >= mFrameLength)
		{
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
					mCurrentBuffer = mCallbacks.allocate();
				}

				// Decrement frame counter
				mCurrentFrame--;
			}
			mFramePayloadBytesReceived = 0;
			mFrameTotalBytesReceived = 0;
		}
	}
	else
	{
		std::cout << "Got error during receive: " << errorCode.value() << " : " << errorCode.message() << " recvd=" << bytesReceived << std::endl;
	}

	if (mAcquiring)
	{

		boost::array<boost::asio::mutable_buffer, 2> rxBufs = {{
			boost::asio::buffer((void*)&mPacketHeader, sizeof(mPacketHeader)),
			boost::asio::buffer(mCurrentBuffer.addr   + mFramePayloadBytesReceived,
					            mCurrentBuffer.length - mFramePayloadBytesReceived) }};

//		mRecvSocket.async_receive_from(boost::asio::buffer(
//				mCurrentBuffer.addr + mFrameTotalBytesReceived,
//				mCurrentBuffer.length - mFrameTotalBytesReceived), mRemoteEndpoint,
//				boost::bind(&FemDataReceiver::handleReceive, this,
//						    boost::asio::placeholders::error,
//						    boost::asio::placeholders::bytes_transferred
//						    )
//		);
		mRecvSocket.async_receive_from(rxBufs, mRemoteEndpoint,
				boost::bind(&FemDataReceiver::handleReceive, this,
						    boost::asio::placeholders::error,
						    boost::asio::placeholders::bytes_transferred
						    )
		);
	}

}
