/*
 * i2c_lm82.c
 *
 *  Created on: 1 Apr 2011
 *      Author: mt47
 */

#include "i2c_lm82.h"

/**
 * Initialises LM82 system monitor chip with high and critical setpoints
 * @param highTemp high temperature setpoint, in degrees celcius
 * @param critTemp critical (shutdown) temperature setpoint, in degrees celcius
 *
 * @return 0 on success, -1 on error
 */
int initLM82(int highTemp, int critTemp)
{
	int numBytes = 0;
	unsigned int payloadSize = 0;
	u8 data[2] = {0,0};

	// Set config register - enable interrupts by setting D3 and D5
	data[0] = LM82_REG_WRITE_CONFIG;
	data[1] = 0x28;
	payloadSize = 2;
	numBytes = writeI2C(IIC_IDX_LM82, IIC_ADDRESS_TEMP, data, payloadSize);
	if (numBytes<payloadSize)
	{
		return -1;
	}

	// Set T_CRIT setpoint to something sensible (power-on default is 127c!)
	data[0] = LM82_REG_WRITE_TCRIT_SP;
	if (critTemp > CRIT_TEMP_MAX) {
		data[1] = CRIT_TEMP_MAX;
	}
	else {
		data[1] = critTemp;
	}
	data[1] = 0x43;		// TODO: REMOVE!
	payloadSize = 2;
	numBytes = writeI2C(IIC_IDX_LM82, IIC_ADDRESS_TEMP, data, payloadSize);
	if (numBytes<payloadSize)
	{
		return -1;
	}

	// Set HIGH setpoint
	data[0] = LM82_REG_WRITE_REMOTE_SP;
	data[1] = highTemp;
	data[1] = 0x43;		// TODO: REMOVE!
	payloadSize = 2;
	numBytes = writeI2C(IIC_IDX_LM82, IIC_ADDRESS_TEMP, data, payloadSize);
	if (numBytes<payloadSize)
	{
		return -1;
	}

	// All OK!
	return 0;
}


/**
 * Reads status register of LM82 device
 * @return status register, 8 bit
 */
u8 readStatus(void)
{
	unsigned int numBytes;
	u8 cmd = LM82_REG_READ_STATUS;
	u8 stat = 0;

	numBytes = writeI2C(IIC_IDX_LM82, IIC_ADDRESS_TEMP, &cmd, 1);
	numBytes = readI2C(IIC_IDX_LM82, IIC_ADDRESS_TEMP, &stat, 1);
	return stat;
}


/**
 * Reads either the local(LM82) or remote(FPGA) temperature
 * @param tempRegCmd either LM82_REG_READ_LOCAL_TEMP or LM82_REG_READ_REMOTE_TEMP
 *
 * @return temperature in degrees celcius, or -1 if an error occured
 */
int readTemp(u8 tempRegCmd)
{
	int numBytes;
	u8 rawVal = 0;

	// Send read command to slave
	numBytes = writeI2C(IIC_IDX_LM82, IIC_ADDRESS_TEMP, &tempRegCmd, 1);
	if (numBytes<1)
	{
		return -1;
	}

	// Grab data byte from slave
	numBytes = readI2C(IIC_IDX_LM82, IIC_ADDRESS_TEMP, &rawVal, 1);
	if (numBytes<1)
	{
		return -1;
	}

	return convertTemperature(rawVal);

}


/**
 * Reads LM82 temperature
 * @return temperature in degrees celcius
 */
int readLocalTemp(void)
{
	return readTemp(LM82_REG_READ_LOCAL_TEMP);
}


/**
 * Reads FPGA temperature
 * @return temperature in degrees celcius
 */
int readRemoteTemp(void)
{
	return readTemp(LM82_REG_READ_REMOTE_TEMP);
}


/**
 * Converts a raw reading from an LM82 (8bit 2s compliment) to degrees celcius
 * @param rawVal raw reading from LM82
 *
 * @return temperature in degrees celcius
 */
int convertTemperature(u8 rawVal)
{
	int temp;

	if (rawVal & 0x80)		// Check MSB for sign bit
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
