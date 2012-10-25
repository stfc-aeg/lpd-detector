/*
 * ExcaliburFemClientScan.cpp
 *
 *  Created on: Oct 24, 2012
 *      Author:  Tim Nicholls, STFC Application Engineering Group
 */

#include "ExcaliburFemClient.h"

void ExcaliburFemClient::dacScanDacSet(unsigned int aDac)
{
	mDacScanDac = aDac;
}

void ExcaliburFemClient::dacScanStartSet(unsigned int aDacStart)
{
	mDacScanStart = aDacStart;
}

void ExcaliburFemClient::dacScanStopSet(unsigned int aDacStop)
{
	mDacScanStop =	aDacStop;
}

void ExcaliburFemClient::dacScanStepSet(unsigned int aDacStep)
{
	mDacScanStep = aDacStep;
}
