/*
 * ExcaliburFemClientAsicControl.cpp - ASIC control methods for the ExcaliburFemClient class
 *
 *  Created on: Dec 16, 2011
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "ExcaliburFemClient.h"
#include "ExcaliburFrontEndDevices.h"
#include "asicControlParameters.h"
#include "mpx3Parameters.h"

/** asicControlOmrSet - setup an OMR value in ASIC control
 *
 * This function sets up an OMR in the ASIC control block, loading
 * top and bottom half of the OMR passed as an argument into the
 * appropriate RDMA registers
 *
 * @param aOmr mpx3OMR object for the OMR to be set
 */
void ExcaliburFemClient::asicControlOmrSet(mpx3Omr aOmr)
{

	// Write bottom and top halves of OMR value into ASIC control RDMA registers
	this->rdmaWrite(kExcaliburAsicOmrBottom, (u32)aOmr.fields.bottom);
	this->rdmaWrite(kExcaliburAsicOmrTop, (u32)aOmr.fields.top);

}

/** asicControlMuxChipSelect - selects a single chip in the ASIC mux
 *
 * This function selects a single chip in the ASIC control mux, for instance
 * to allow parameters to be uploaded to a single chip.
 *
 * @param aChipIdx index of chip (0-7) to be enabled in the mux
 */
void ExcaliburFemClient::asicControlMuxChipSelect(unsigned int aChipIdx)
{
	// Generate the mux select value (chip 0 is at top of mux)
	u32 muxSelectVal = ((u32)1 << (7 - aChipIdx));

	// Write generated value into ASIC control mux select register
	this->rdmaWrite(kExcaliburAsicMuxSelect, muxSelectVal);

}

/** asicControlCommandExecute - execute an ASIC command
 *
 * This function executes an ASIC by writing to the ASIC control
 * command word register, which triggers an OMR-based transaction
 * to the ASIC. The appropriate OMR must have already been setup
 * in the FEM by a call to asicControlOmrSet.
 *
 * @param aCommand ASIC control command to execute
 */
void ExcaliburFemClient::asicControlCommandExecute(asicControlCommand aCommand)
{

	// Execute the command by writing to the command word register
	this->rdmaWrite(kExcaliburAsicControlReg, (u32)aCommand);

}

/** asicControlReset - reset the ASIC control firmware block
 *
 * This function resets the ASIC control firmware block, resetting
 * its internal state machine back to the default and clearing any
 * incomplete ASIC transactions
 */
void ExcaliburFemClient::asicControlReset(void)
{

	// Toggle reset bit in ASIC control register
	this->rdmaWrite(kExcaliburAsicControlReg, 0x400000);
	this->rdmaWrite(kExcaliburAsicControlReg, 0x0);

}

/** asicControlAsicReset - reset the ASICs
 *
 * This function resets all ASICs connected to the FEM by asserting
 * the reset condition.
 */
void ExcaliburFemClient::asicControlAsicReset(void)
{

	// Toggle ASIC reset bit (23) in ASIC control register
	this->rdmaWrite(kExcaliburAsicControlReg, 0x800000);
	this->rdmaWrite(kExcaliburAsicControlReg, 0x0);

}

/** asicControlNumFramesSet - set the number of frames to acquire
 *
 * This function sets the number of frames to acquire in the ASIC
 * control firmware block of the FEM.
 *
 * @param aNumFrames number of frames to acquire
 */
void ExcaliburFemClient::asicControlNumFramesSet(unsigned int aNumFrames)
{
	// Set number of frames in ASIC control RDMA register
	this->rdmaWrite(kExcaliburAsicFrameCounter, (u32)aNumFrames);
}

/** asicControlShutterDurationSet - set the ASIC shutter duration in microseconds
 *
 * This function sets up the internal shutter duration in microseconds. There
 * are two registers in the ASIC control block, setting the shutter resolution
 * and the shutter counter. We run with a fixed resolution of 500ns, so the
 * shuttter counter should be twice the argument specified in microseconds
 *
 * @param aTimeUs shutter duration in microseconds
 */
void ExcaliburFemClient::asicControlShutterDurationSet(unsigned int aTimeUs)
{

	u32 shutterCounter = aTimeUs * 2;

	// Set constant shutter resolution of 500ns = 0x64
	this->rdmaWrite(kExcaliburAsicShutterResolution, 0x64);

	// Set both shutter 0 and shutter 1 counters to value in 500ns steps
	this->rdmaWrite(kExcaliburAsicShutter0Counter, shutterCounter);
	this->rdmaWrite(kExcaliburAsicShutter1Counter, shutterCounter);

}

/** asicControlCounterDepthSet - set the ASIC pixel counter depth
 *
 * This function sets up the ASIC control block pixel counter depth. Note
 * that this is NOT the setup for the ASIC itself, which is done through the
 * OMR, but for the readout block. The two values MUST match.
 *
 * @param aCounterDepth enumerated counter depth from MPX3 setttings
 */
void ExcaliburFemClient::asicControlCounterDepthSet(mpx3CounterDepth aCounterDepth)
{

	u32 counterBitDepth = this->counterBitDepth(aCounterDepth);

	// Throw exception if illegal counter depth specified
	if (counterBitDepth == 0)
	{
		std::ostringstream msg;
		msg << "Illegal counter depth specified: " << aCounterDepth;
		throw FemClientException((FemClientErrorCode)excaliburFemClientIllegalCounterDepth, msg.str());
	}

	// Set up the counter depth in the RDMA register
	this->rdmaWrite(kExcaliburAsicPixelCounterDepth, counterBitDepth);

}

void ExcaliburFemClient::asicControlReadoutLengthSet(unsigned int aLength)
{
	this->rdmaWrite(kExcaliburAsicReadoutLength, (u32)aLength);
}

