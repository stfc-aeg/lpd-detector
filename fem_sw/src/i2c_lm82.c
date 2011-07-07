/*
 * i2c_lm82.c
 *
 *  Created on: 1 Apr 2011
 *      Author: mt47
 */

#include "i2c_lm82.h"

// Configures and writes initial setpoints to LM82 monitoring chip
void initLM82(int highTemp, int critTemp)
{
	unsigned int numBytes = 0;
	unsigned int payloadSize = 0;
	u8 data[2] = {0,0};

	// TODO: Should we check if high>crit and flag a warning or reverse their values?

	// Set config register
	data[0] = LM82_REG_WRITE_CONFIG;
	data[1] = 0x28;	// D3 - remote T_CRIT mask, D5 - local T_CRIT mask
	payloadSize = 2;
	numBytes = writeI2C(IIC_ADDRESS_TEMP, data, payloadSize);
	if (numBytes<payloadSize)
	{
		// TODO: Error
	}

	// Set T_CRIT setpoint to something sensible (power-on default is 127c!)
	data[0] = LM82_REG_WRITE_TCRIT_SP;
	if (critTemp > CRIT_TEMP_MAX) {
		data[1] = CRIT_TEMP_MAX;
	}
	else {
		data[1] = critTemp;
	}
	payloadSize = 2;
	numBytes = writeI2C(IIC_ADDRESS_TEMP, data, payloadSize);
	if (numBytes<payloadSize)
	{
		// TODO: Error
	}

	// Set HIGH setpoint
	// TODO: We only set remote HIGH SP, can we leave local at 127 (power on default) ?
	data[0] = LM82_REG_WRITE_REMOTE_SP;
	data[1] = highTemp;
	payloadSize = 2;
	numBytes = writeI2C(IIC_ADDRESS_TEMP, data, payloadSize);
	if (numBytes<payloadSize)
	{
		// TODO: Error
	}

}

// Reads status register
u8 readStatus(void)
{
	unsigned int numBytes;
	u8 cmd = LM82_REG_READ_STATUS;
	u8 stat = 0;

	// TODO: Error handling

	numBytes = writeI2C(IIC_ADDRESS_TEMP, &cmd, 1);
	numBytes = readI2C(IIC_ADDRESS_TEMP, &stat, 1);
	return stat;
}

// Reads remote (FPGA) temperature
int readTemp(u8 tempRegCmd)
{
	unsigned int numBytes;
	u8 rawVal = 0;

	// Send read command to slave
	numBytes = writeI2C(IIC_ADDRESS_TEMP, &tempRegCmd, 1);
	if (numBytes<1)
	{
		// TODO: Error handling
	}

	// Grab data byte from slave
	numBytes = readI2C(IIC_ADDRESS_TEMP, &rawVal, 1);
	if (numBytes<1)
	{
		// TODO: Error handling
	}

	return convertTemperature(rawVal);

}

// Reads local LM82 temperature
int readLocalTemp(void)
{
	return readTemp(LM82_REG_READ_LOCAL_TEMP);
}

// Reads remote LM82 temperature (i.e. FPGA temp)
int readRemoteTemp(void)
{
	return readTemp(LM82_REG_READ_REMOTE_TEMP);
}

// Converts temperature from 8bit 2s compliment value to degrees celcius
int convertTemperature(u8 rawVal)
{
	int temp;

	// Check MSB for sign bit
	if (rawVal & 0x80)
	{
		// Negative
		temp = ((int)~rawVal) + 1;
	}
	else
	{
		// Positive
		temp = (int)rawVal;
	}

	return temp;
}
