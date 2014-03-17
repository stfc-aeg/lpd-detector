/*
 * FemDataReceiver.cpp
 *
 *  Created on: 7 Dec 2011
 *      Author: tcn
 */

#include "FemClient.h"
#include "FemDataReceiver.h"
#include <time.h>

#ifdef SCRATCH_BUFFER
void* lScratchBuffer = 0;
#endif

FemDataReceiver::FemDataReceiver(unsigned int aRecvPort)
	: mRecvPort(aRecvPort),
	  mRecvSocket(mIoService, boost::asio::ip::udp::endpoint(boost::asio::ip::udp::v4(), aRecvPort)),
	  mWatchdogTimer(mIoService),
	  mAcquiring(false),
	  mStopped(false),
	  mReceiverTerminated(false),
	  mRemainingFrames(0),
	  mNumFrames(0),
	  mFrameLength(0),
	  mHeaderPosition(headerAtStart),
	  mAcquisitionPeriod(0),
	  mAcquisitionTime(0),
	  mNumSubFrames(1),
	  mSubFrameLength(0),
	  mEnableFrameCounterCheck(true),
	  mFrameTotalBytesReceived(0),
	  mFramePayloadBytesReceived(0)
{
	int nativeSocket = (int)mRecvSocket.native_handle();
	int rcvBufSize = 8388608;
	int rc = setsockopt(nativeSocket, SOL_SOCKET, SO_RCVBUF, (void*)&rcvBufSize, sizeof(rcvBufSize));
	if (rc != 0)
	{
		std::cout << "setsockopt failed" << std::endl;
	}
}

FemDataReceiver::~FemDataReceiver()
{

	// Make sure the IO service is stopped and the receiver thread terminated before destroying this object
	//this->stopAcquisition(0);

}

void FemDataReceiver::startAcquisition(void)
{

	if (!mAcquiring) {

#ifdef SCRATCH_BUFFER
		lScratchBuffer = malloc(mFrameLength*4);
		if (lScratchBuffer == 0) {
			std::cout << "FATAL could not allocate scratch buffer";
			return;
		}
#endif

		std::cout << "Starting acquisition loop for " << mNumFrames <<  " frames" << std::endl;

		// Clear stopped flag
		mStopped = false;
		mReceiverTerminated = false;

		// Set acquisition flag
		mAcquiring = true;

		// Initialise current frame counter to number of frames to be acquired
		mRemainingFrames = mNumFrames;

		// Zero complete-after flag - a non-zero value inserted here by an asynchronous stop
		// command will allow clean termination of the receiver after the specified number
		// of frames
		mCompleteAfterNumFrames = 0;

		// Initialise counters for next frame acquisition sequence
		mFramePayloadBytesReceived = 0;
		mFrameTotalBytesReceived   = 0;
		mSubFramesReceived         = 0;
		mSubFramePacketsReceived   = 0;
		mSubFrameBytesReceived     = 0;
		mFramesReceived            = 0;
		mLatchedFrameNumber        = 0;

		// Initialise subframe length
		mSubFrameLength = mFrameLength / mNumSubFrames;

		// Initialise latched error signal
		mLatchedErrorSignal = FemDataReceiverSignal::femAcquisitionNullSignal;

		if (mCallbacks.allocate)
		{

			// Pre-allocate an initial buffer via the callback
			mCurrentBuffer = mCallbacks.allocate();

			// If the IO service is stopped (i.e. the receiver has been run before), restart it
			// and check that it is running OK
			if (mIoService.stopped())
			{
				std::cout << "Resetting IO service" << std::endl;
				mIoService.reset();
			}

			if (mIoService.stopped())
			{
				std::cout << "Resetting IO service FAILED" << std::endl;
				// TODO handle error here
			}

			if (!mRecvSocket.is_open()) {
				std::cout << "Reopening UDP receive socket on port " << mRecvPort << std::endl;
				mRecvSocket.open(boost::asio::ip::udp::v4());
				mRecvSocket.bind(boost::asio::ip::udp::endpoint(
					      boost::asio::ip::udp::v4(), mRecvPort));
				if (mRecvSocket.is_open())
				{
					std::cout << "UDP receive socket is now reopened OK" << std::endl;
				} else {
					std::cout << "UDP receive socket failed to reopen" << std::endl;
				}


			}
#ifdef SIMULATED_RECEIVER

			// Launch a simulated receive handler using a deadline actor, set to run on the
			// watchdog timer at the acquisition period interval. This simulates reception of
			// frames by calling the receive callback and requesting a new buffer
			mWatchdogTimer.expires_from_now(boost::posix_time::milliseconds(mAcquisitionPeriod));
			simulateRecieve();

#else
			// Launch async receive on UDP socket - we provide an array of boost mutable buffers
			// that allow the receive to function in scatter/gather mode, where the packet header,
			// payload and frame counter are written to separate locations.
			boost::array<boost::asio::mutable_buffer, 3> rxBufs;
			if (mHeaderPosition == headerAtStart)
			{
				rxBufs[0] = boost::asio::buffer((void*)&mPacketHeader, sizeof(mPacketHeader));

#ifdef SCRATCH_BUFFER
				//rxBufs[1] = boost::asio::buffer(mScratchBuffer, mSubFrameLength);
#else
				rxBufs[1] = boost::asio::buffer(mCurrentBuffer.addr, mSubFrameLength);
#endif
				rxBufs[2] = boost::asio::buffer((void*)&mCurrentFrameNumber, sizeof(mCurrentFrameNumber));
			}
			else
			{
#ifdef SCRATCH_BUFFER
				//rxBufs[0] = boost::asio::buffer(mScratchBuffer, mSubFrameLength);
#else
				rxBufs[0] = boost::asio::buffer(mCurrentBuffer.addr, mSubFrameLength);
#endif
				rxBufs[1] = boost::asio::buffer((void*)&mPacketHeader, sizeof(mPacketHeader));
				rxBufs[2] = boost::asio::buffer((void*)&mCurrentFrameNumber, sizeof(mCurrentFrameNumber));
			}

			mRecvSocket.async_receive_from(rxBufs, mRemoteEndpoint,
					boost::bind(&FemDataReceiver::handleReceive, this,
							    boost::asio::placeholders::error,
							    boost::asio::placeholders::bytes_transferred
							    )
			);

			// Setup watchdog handler deadline actor to handle receive timeouts
			mRecvWatchdogCounter = 0;
//			mWatchdogTimer.expires_from_now(boost::posix_time::milliseconds(kWatchdogHandlerIntervalMs));
//			watchdogHandler();
#endif



			// Launch a thread to start the io_service for receiving data, running the watchdog etc
			mReceiverThread = boost::shared_ptr<boost::thread>(new boost::thread(
					boost::bind(&boost::asio::io_service::run, &mIoService)));

		}
		else
		{
			std::cout << "Callbacks not initialised, cannot start receiver" << std::endl;
		}
	} else {
		std::cout << "ERROR: acquiring flag set on start acquisition" << std::endl;
	}

}

void FemDataReceiver::stopAcquisition(unsigned int aNumFrames)
{

	int numCompleteLoops = 0;
	const int maxCompleteLoops = 5000;

	// Set the complete-after flag to number of frames specified. This allows
	// an asynchronous stop even if there are still frames remaining to receive
	mCompleteAfterNumFrames = aNumFrames;

	if (mCompleteAfterNumFrames) {

		std::cout << "Waiting for data receiver thread to complete after "
				  << mCompleteAfterNumFrames << " frames. Current number of frames received: "
				  << mFramesReceived << std::endl;

		// Wait for receiver to complete otherwise timeout
		while ((mFramesReceived < mCompleteAfterNumFrames) && (numCompleteLoops < maxCompleteLoops))
		{
			usleep(1000);
			numCompleteLoops++;
		}
		if (mFramesReceived < mCompleteAfterNumFrames)
		{
			std::cout << "ERROR: timeout during asynchronous completion of acquisition receiver" << std::endl;
		} else {
			std::cout << "Acquisition completed" << std::endl;
		}
	}

	mAcquiring = false;
	mStopped = true;
//	mWatchdogTimer.cancel();
	mRecvSocket.close();

	numCompleteLoops = 0;
	while ((mReceiverTerminated != true) && (numCompleteLoops < maxCompleteLoops))
	{
		usleep(1000);
		numCompleteLoops++;
	}
	if (!mReceiverTerminated)
	{
		std::cout << "ERROR: timeout during receive handler termination" << std::endl;
	}
	else
	{
		std::cout << "Receive handler terminated correctly" << std::endl;
	}

	// Stop the IO service to allow the receive thread to terminate gracefully
	if (!mIoService.stopped())
	{
		mIoService.stop();
		std::cout << "Stopping asynchronous IO service" << std::endl;
	} else {
		std::cout << "Asynchronous IO service already stopped" << std::endl;
	}

	if (mRecvSocket.is_open()) {
		std::cout << "Receive socket is still open" << std::endl;
	} else {
		std::cout << "Receive socket is now closed" << std::endl;
	}

	if (mCompleteAfterNumFrames) {
		mCallbacks.signal(FemDataReceiverSignal::femAcquisitionComplete);
	}

#ifdef SCRATCH_BUFFER
	if (lScratchBuffer != 0)
	{
		free(lScratchBuffer);
		lScratchBuffer = 0;
	}
#endif

}

bool FemDataReceiver::acqusitionActive(void)
{
	return mAcquiring;
}


void FemDataReceiver::setNumFrames(unsigned int aNumFrames)
{
	mNumFrames = aNumFrames;
}

void FemDataReceiver::setFrameLength(unsigned int aFrameLength)
{
	mFrameLength = aFrameLength;
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

void FemDataReceiver::setNumSubFrames(unsigned int aNumSubFrames)
{
	mNumSubFrames = aNumSubFrames;
}

void FemDataReceiver::enableFrameCounterCheck(bool aEnable)
{
	mEnableFrameCounterCheck = aEnable;
}


void FemDataReceiver::registerCallbacks(CallbackBundle* aBundle)
{
	mCallbacks = *aBundle;
}

void FemDataReceiver::watchdogHandler(void)
{
	if (mStopped)
	{
		std::cout << "watchdogHandler stopping with flag" << std::endl;
		return;
	}
	if (mWatchdogTimer.expires_at() <= boost::asio::deadline_timer::traits_type::now())
	{

		// Check if receive watchdog counter has been not been cleared

		// Increment watchdog counter - this will be reset to zero by the
		// receive handler every time a receive occurs
		mRecvWatchdogCounter++;

		// If an asynchronous stop has been been signalled, stop when the correct number of frames is reached
		// The watchdog handler must deal with this condition since the receiver spends more time blocked
		// waiting for packet reception
		if (mCompleteAfterNumFrames)
		{
			unsigned int numFramesReceived = mNumFrames - mRemainingFrames;

			if (numFramesReceived >= mCompleteAfterNumFrames)
			{
				std::cout << "Receiver asynchronous stop: received " << numFramesReceived << " frames, stopping" << std::endl;
//				mCallbacks.signal(FemDataReceiverSignal::femAcquisitionComplete);

				mAcquiring = false;

			}
		}

		// Reset deadline timer
		mWatchdogTimer.expires_from_now(boost::posix_time::milliseconds(kWatchdogHandlerIntervalMs));

	}

	// If acquisition is still running, restart watchdog to call this handler
	if (mAcquiring)
	{
		mWatchdogTimer.async_wait(boost::bind(&FemDataReceiver::watchdogHandler, this));
	}
	else {
//		std::cout << "Watchdog timer is terminating" << std::endl;
	}

}

void FemDataReceiver::simulateReceive(BufferInfo aBuffer)
{
	BufferInfo buffer = aBuffer;

	if (mWatchdogTimer.expires_at() <= boost::asio::deadline_timer::traits_type::now())
	{
		// Flag current buffer as received
		if (mCallbacks.receive)
		{
			time_t now;
			time(&now);
			mCallbacks.receive(mRemainingFrames, now);
		}

		if (mRemainingFrames == 1)
		{
			// On last frame, stop acq loop and signal completion
			mCallbacks.signal(FemDataReceiverSignal::femAcquisitionComplete);
			mAcquiring = false;
		}
		else if (mRemainingFrames == 0)
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
			mWatchdogTimer.expires_from_now(boost::posix_time::milliseconds(mAcquisitionPeriod));

			// Decrement current frame counter
			mRemainingFrames--;
		}

	}
	if (mAcquiring)
	{
		mWatchdogTimer.async_wait(boost::bind(&FemDataReceiver::simulateReceive, this, buffer));
	}

	// Reset watchdog counter
	mRecvWatchdogCounter = 0;
}

void FemDataReceiver::handleReceive(const boost::system::error_code& errorCode, std::size_t bytesReceived)
{

	time_t recvTime;
	FemDataReceiverSignal::FemDataReceiverSignals errorSignal = FemDataReceiverSignal::femAcquisitionNullSignal;

	if (mStopped)
	{
		std::cout << "Receive handler terminating on stopped flag" << std::endl;
		mReceiverTerminated = true;
		return;
	}

	if (!errorCode && bytesReceived > 0)
	{

		unsigned int payloadBytesReceived = bytesReceived - mFrameHeaderLength;

		// Update Total amount of data received in this frame so far including headers
		mFrameTotalBytesReceived   += bytesReceived;

		// Update total payload data received in this subframe so far
		mSubFrameBytesReceived     += payloadBytesReceived;

		// Update total payload data received in this subframe so far, minus packet headers and any frame counters recevied
		// at the end of each subframe
		mFramePayloadBytesReceived += payloadBytesReceived;

		// DEBUG output
//		std::cout << std::hex << mPacketHeader.frameNumber << " " << mPacketHeader.packetNumberFlags << std::dec << " "
//				  << bytesReceived << " " << mFrameTotalBytesReceived << " " << mFramePayloadBytesReceived << " "
//				  << mSubFramesReceived << " " << mSubFramePacketsReceived << " "
//				  << (mCurrentBuffer.length - mFramePayloadBytesReceived) << " "
//				  << mSubFrameBytesReceived << std::endl;

		// If this is the first packet in a sub-frame, we expect packet header to have SOF marker and packet number to
		// be zero. Otherwise, check that the packet number is incrementing correctly, i.e. we have not dropped any
		// packets
		if (mSubFramePacketsReceived == 0)
		{
			if (!(mPacketHeader.packetNumberFlags & kStartOfFrameMarker))
			{
				std::cout << "Missing SOF marker on packet. Header info: frame: " << mPacketHeader.frameNumber
						  << " packet number/flags: " << mPacketHeader.packetNumberFlags << std::endl;
				errorSignal = FemDataReceiverSignal::femAcquisitionCorruptImage;
			}
			else
			{
				mSubFramePacketsReceived++;
			}
		}
		else
		{
			// Check packet number is incrementing as expected within subframe
			if ((mPacketHeader.packetNumberFlags & kPacketNumberMask) != mSubFramePacketsReceived)
			{
				std::cout << "Incorrect packet number sequence, got: " << (mPacketHeader.packetNumberFlags & kPacketNumberMask)
						  << " expected: " << mSubFramePacketsReceived << std::endl;
				errorSignal = FemDataReceiverSignal::femAcquisitionCorruptImage;

			}

			// Check for EOF marker in packet header, if so, test sanity of frame counters, handle
			// end-of-subframe bookkeeping, reset subframe packet and data counters and increment
			// number of subframes received
			if (mPacketHeader.packetNumberFlags & kEndOfFrameMarker)
			{

//				std::cout << "EOF CUR: " << mCurrentFrameNumber << " LAT: " << mLatchedFrameNumber << " SUB: "
//						  <<mSubFramesReceived << " FRA: " << mFramesReceived << " REM: " << mRemainingFrames << std::endl;

				// Timestamp reception of last packet of frame
				time(&recvTime);

				// If this is the first subframe, store the frame counter from the end
				// of the frame and check it is incrementing correctly from the last
				// frame, otherwise check that they agree across subframes
				if (mSubFramesReceived == 0)
				{
					if (mEnableFrameCounterCheck) {

						if (mCurrentFrameNumber != (mLatchedFrameNumber+1))
						{
							std::cout << "Incorrect frame counter on first subframe, got: " << mCurrentFrameNumber
									  << " expected: " << mLatchedFrameNumber+1
									  << " frames recieved: " << mFramesReceived << std::endl;
							errorSignal = FemDataReceiverSignal::femAcquisitionCorruptImage;

						}
					} else {
						mCurrentFrameNumber = mLatchedFrameNumber + 1;
					}
					mLatchedFrameNumber = mCurrentFrameNumber;
				}
				else
				{
					if (mEnableFrameCounterCheck) {
						if (mCurrentFrameNumber != mLatchedFrameNumber)
						{
							std::cout << "Incorrect frame counter in subframe, got: " << mCurrentFrameNumber
									  << " expected: " << mLatchedFrameNumber << std::endl;
							errorSignal = FemDataReceiverSignal::femAcquisitionCorruptImage;

						}
					}
				}

				// Decrement subframe and frame payload bytes received to account for frame counter
				// appended to last packet
				mSubFrameBytesReceived -= sizeof(mCurrentFrameNumber);
				mFramePayloadBytesReceived -= sizeof(mCurrentFrameNumber);

				// Increment number of subframes received
				mSubFramesReceived++;

				// If the number of subframes received matches the number expected for the
				// frame, check that we have received the correct amount of data
				if (mSubFramesReceived == mNumSubFrames)
				{
					if (mFramePayloadBytesReceived != mFrameLength)
					{
						std::cout << "Received complete frame with incorrect size, got " << mFramePayloadBytesReceived
								  << " expected " << mFrameLength << std::endl;
						errorSignal = FemDataReceiverSignal::femAcquisitionCorruptImage;

					}
					else
					{
						//std::cout << "Frame completed OK counter = " << mCurrentFrameNumber << std::endl;
					}
					mFramesReceived++;
				}

				// Reset subframe counters
				mSubFramePacketsReceived = 0;
				mSubFrameBytesReceived   = 0;
			}
			else
			{
				mSubFramePacketsReceived++;
			}
		}

		if (mFramePayloadBytesReceived > mFrameLength)
		{
			std::cout << "Buffer overrun detected in receive of frame number " << mCurrentFrameNumber
					  << " subframe " << mSubFramesReceived << " packet " << mSubFramePacketsReceived << std::endl;
			errorSignal = FemDataReceiverSignal::femAcquisitionCorruptImage;
		}

		// Signal current buffer as received if completed, and request a new one unless
		// we are on the last frame, in which case signal acquisition complete. Also
		// detect if an asynchronous abort has been flagged
		if (mFramePayloadBytesReceived >= mFrameLength)
		{
			if (mCallbacks.receive)
			{
				mCallbacks.receive(mCurrentFrameNumber, recvTime);
			}

			if (mCompleteAfterNumFrames != 0)
			{
				std::cout << "Async stop after " << mCompleteAfterNumFrames << " requested, frames received: "
						<< mFramesReceived << std::endl;

				mAcquiring = false;
				mReceiverTerminated = true;
				mCallbacks.signal(FemDataReceiverSignal::femAcquisitionComplete);
			}
			if (mRemainingFrames == 1)
			{
				// On last frame, stop acquisition loop and signal completion
				mAcquiring = false;
				mReceiverTerminated = true;
				mCallbacks.signal(FemDataReceiverSignal::femAcquisitionComplete);
			}
			else if (mRemainingFrames == 0)
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

				// Decrement remaining frame counter
				mRemainingFrames--;
			}

			// Reset frame counters
			mFramePayloadBytesReceived = 0;
			mFrameTotalBytesReceived   = 0;
			mSubFramePacketsReceived   = 0;
			mSubFramesReceived         = 0;
			mSubFrameBytesReceived     = 0;

			// Reset latched error signal
			mLatchedErrorSignal = FemDataReceiverSignal::femAcquisitionNullSignal;
		}
	}
	else
	{
		if (errorCode.value() == boost::asio::error::operation_aborted) {
			std::cout << "Receive operation aborted due to cancel, terminating readout" << std::endl;
			mAcquiring = false;
			mReceiverTerminated = true;
		} else {
			std::cout << "Got error during receive: " << errorCode.value() << " : " << errorCode.message() << " recvd=" << bytesReceived << std::endl;
			errorSignal = FemDataReceiverSignal::femAcquisitionCorruptImage;
		}
	}

	// If an error condition has been set during packet decoding, signal it through the callback only if the
	// value has changed, so that this is only done once per frame
	if ((errorSignal != FemDataReceiverSignal::femAcquisitionNullSignal) && (errorSignal != mLatchedErrorSignal))
	{
		mCallbacks.signal(errorSignal);
		mLatchedErrorSignal = errorSignal;
	}

	if (mAcquiring)
	{

		// Construct buffer sequence for reception of next packet header and payload. Payload buffer
		// points to the next position in the current buffer

		boost::array<boost::asio::mutable_buffer, 3> rxBufs;
		if (mHeaderPosition == headerAtStart)
		{
			rxBufs[0] = boost::asio::buffer((void*)&mPacketHeader, sizeof(mPacketHeader));
#ifdef SCRATCH_BUFFER
			rxBufs[1] = boost::asio::buffer(lScratchBuffer, mSubFrameLength - mSubFrameBytesReceived);
#else
			rxBufs[1] = boost::asio::buffer(mCurrentBuffer.addr   + mFramePayloadBytesReceived,
					                        mSubFrameLength - mSubFrameBytesReceived);
#endif
			rxBufs[2] = boost::asio::buffer((void*)&mCurrentFrameNumber, sizeof(mCurrentFrameNumber));
		}
		else
		{
			rxBufs[1] = boost::asio::buffer((void*)&mPacketHeader, sizeof(mPacketHeader));
#ifdef SCRATCH_BUFFER
			rxBufs[0] = boost::asio::buffer(lScratchBuffer, mSubFrameLength - mSubFrameBytesReceived);
#else
			rxBufs[0] = boost::asio::buffer(mCurrentBuffer.addr   + mFramePayloadBytesReceived,
                                            mSubFrameLength - mSubFrameBytesReceived);
#endif
			rxBufs[2] = boost::asio::buffer((void*)&mCurrentFrameNumber, sizeof(mCurrentFrameNumber));
		}

		// Launch the asynchronous receive onto this handler
		mRecvSocket.async_receive_from(rxBufs, mRemoteEndpoint,
				boost::bind(&FemDataReceiver::handleReceive, this,
						    boost::asio::placeholders::error,
						    boost::asio::placeholders::bytes_transferred
						    )
		);
	}
	else {
		std::cout << "Receiver handler terminating at end of final frame" << std::endl;
		mReceiverTerminated = true;
	}

	// Reset receive watchdog counter
	mRecvWatchdogCounter = 0;

}
