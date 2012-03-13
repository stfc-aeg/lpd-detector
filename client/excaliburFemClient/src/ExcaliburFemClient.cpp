/*
 * ExcaliburFemClient.cpp
 *
 *  Created on: 7 Dec 2011
 *      Author: tcn
 */

#include "ExcaliburFemClient.h"
#include "ExcaliburFrontEndDevices.h"
#include "time.h"

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

	// Temp hack to test recveier
	mFemDataReceiver.setFrameLength(98304*2);
	mFemDataReceiver.setFrameHeaderLength(8);

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

void ExcaliburFemClient::setFrontEndEnable(unsigned int aVal)
{

	// Construct byte value to send to device. Since only bit 0 is RW,
	// we mask this out of requested value and force other bits to 1
	// to retain input function (which monitor supply regulator status).

	unsigned int writeVal = (aVal & 0x1) | (0xFE);

	// Write to the IO device
	this->frontEndPCF8574Write(writeVal);

}


double ExcaliburFemClient::frontEndTemperatureRead(void)
{

	u16 rawVal = this->frontEndSht21Read(kSHT21TemperatureCmd);

	double temperature = -46.85 + (175.72 * ((double)rawVal / 65536.0));

	return temperature;
}

double ExcaliburFemClient::frontEndHumidityRead(void)
{
	u16 rawVal = this->frontEndSht21Read(kSHT21HumidityCmd);

	double humidity = -6.0 + (125.0 * ((double)rawVal / 65536.0));

	return humidity;
}

double ExcaliburFemClient::frontEndDacOutRead(unsigned int aChipId)
{

	// Map chipId into ADC device channel
	unsigned int device = aChipId / 4;
	unsigned int chan = kAD7994ChipMap[aChipId % 4];

	// Acquire ADC value
	u16 rawAdcValue = this->frontEndAD7994Read(device, chan);

	// Convert ADC units to volts (2V reference) and return
	double adcValue = 0.5 * (double)rawAdcValue;

	return adcValue;
}

int ExcaliburFemClient::frontEndSupplyStatusRead(excaliburFrontEndSupply aSupply)
{

	// Read IO values from PCF
	u8 pcfValue = this->frontEndPCF8574Read();

	// Extract appropriate bit from the value and return;
	int status = (pcfValue >> aSupply) & 0x1;

	return status;

}

void ExcaliburFemClient::frontEndDacInWrite(unsigned int aChipId, unsigned int aDacValue)
{

	// Map chipId onto DAC device and channel. Chips 4,3,2,1 on DAC0, 8,7,6,5 on DAC1
	unsigned int device = aChipId / 4;
	unsigned int chan   = kAD5625ChipMap[aChipId % 4];

	// Write the DAC value
	this->frontEndAD5625Write(device, chan, aDacValue);

}

u16 ExcaliburFemClient::frontEndSht21Read(u8 aCmdByte)
{

	// Send conversion command to device
	std::vector<u8>cmd(1, aCmdByte);
	this->i2cWrite(kSHT21Address, cmd);

	// Wait 100ms
	struct timespec sleep;
	sleep.tv_sec = 0;
	sleep.tv_nsec = 100000000;
	nanosleep(&sleep, NULL);

	// Read three bytes back
	std::vector<u8> response = this->i2cRead(kSHT21Address, 3);

	u16 rawVal = (((u16)response[0]) << 8) | response[1];

	return rawVal;
}

u16 ExcaliburFemClient::frontEndAD7994Read(unsigned int aDevice, unsigned int aChan)
{

	// Calculate address pointer to send to ADC
	u8 addrPtr = 1 << (aChan+4);

	// Send channel select command to AD
	std::vector<u8>cmd(2);
	cmd[0] = 0;
	cmd[1] = addrPtr;

	this->i2cWrite(kAD7994Address[aDevice], cmd);

	// TODO - wait for conversion?

	// Read two bytes back
	std::vector<u8> response = this->i2cRead(kAD7994Address[aDevice], 2);

	// Decode ADC value to return
	u16 adcVal = ((((u16)response[0]) << 8) | response[1]) & 0x7FF;

	return adcVal;
}

u8 ExcaliburFemClient::frontEndPCF8574Read(void)
{
	// Read a single byte from the device
	std::vector<u8> response = this->i2cRead(kPCF8574Address, 1);

	// Return value
	return response[0];

}

void ExcaliburFemClient::frontEndPCF8574Write(unsigned int aVal)
{

	std::vector<u8> cmd(1);

	// Construct single byte to write to device
	cmd[0] = (u8)(aVal & 0xFF);

	// Send command
	this->i2cWrite(kPCF8574Address, cmd);

}

void ExcaliburFemClient::frontEndAD5625Write(unsigned int aDevice, unsigned int aChan, unsigned int aVal)
{

	std::vector<u8>cmd(3); // 3 byte write transaction to DAC

	// Assemble command byte from command and DAC channel
	cmd[0] = (kAD5626CmdMode << kAD5625CmdShift) | (aChan & 0x7);

	// Assemble two bytes of DAC value shifted up
	u16 dacWord = aVal << kAD5625DacShift;
	cmd[1] = (dacWord & 0xFF00) >> 8;
	cmd[2] = (dacWord & 0x00FF);

	// Send transaction to DAC
	this->i2cWrite(kAD5625Address[aDevice], cmd);

}
