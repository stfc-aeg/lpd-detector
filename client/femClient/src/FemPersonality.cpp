/*
 * FemPersonality.cpp
 *
 *  Created on: Mar 23, 2012
 *      Author: gm
 */
#include "FemClient.h"

/** write - execute a personality write transaction on the connected FEM
 *
 * This function executes a write transaction on the connected FEM.
 *
 * @param subCommand
 * @param aWidth width of each write (byte, word, long)
 * @param streamMask address of first write transaction
 * @param aPayload vector of writes of appropriate width
 * @param size size of payload in bytes
 * @return number of writes completed in transaction
 */
u32 FemClient::personalityWrite(unsigned int subCommand, unsigned int aWidth, unsigned int streamMask,
					u8* aPayload, std::size_t size)
{
	// Create a write transaction based on the specified bus, width, address and payload
	// parameters.
	u8 state = 0;
	SBIT(state, STATE_WRITE);
	FemTransaction request(CMD_PERSONALITY, subCommand, aWidth, state, streamMask, aPayload, size);

	// Send the write transaction
	this->send(request.encodeArray());

	// Receive the response
	u_int32_t payload[] = { 0 };
	FemTransaction response = this->receive((u8*)payload);

	// Check for an ACK and the absence of a NACK on the response
	u8 responseState = response.getState();
	if (!(CMPBIT(responseState, STATE_ACK)) || (CMPBIT(responseState, STATE_NACK))) {
		std::ostringstream msg;
		msg << "FEM response did not acknowledge write transaction of sub command " << subCommand << " to stream mask " << streamMask;
		throw FemClientException(femClientMissingAck, msg.str());
	}

	return response.payloadLength();
}



