/*
 * FemClientAcquisition.cpp
 *
 *  Created on: Mar 16, 2012
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "FemClient.h"
#include "FemException.h"


void FemClient::acquireConfig(u32 aAcqMode, u32 aBufferSize, u32 aBufferCount, u32 aNumAcq)
{

	protocol_acq_config config = { aAcqMode, aBufferSize, aBufferCount, aNumAcq };

	this->commandAcquire(CMD_ACQ_CONFIG, &config);
}

void FemClient::acquireStart(void)
{

	this->commandAcquire(CMD_ACQ_START, NULL);
}

void FemClient::acquireStop(void)
{
	this->commandAcquire(CMD_ACQ_STOP, NULL);
}

void FemClient::acquireStatus(void)
{
	this->commandAcquire(CMD_ACQ_STATUS, NULL);
}
