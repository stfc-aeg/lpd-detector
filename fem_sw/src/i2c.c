/*
 * i2c.c
 *
 * I2C abstraction layer for Xilinx
 *
 */

#include "i2c.h"

// Writes data to slave on I2C bus as master, issues stop after data.
// Returns number of bytes sent over wire
int writeI2C(u8 slaveAddr, u8* pData, unsigned dataLen)
{
	int numBytes = 0;
	// TODO: Expend this to deal with errors (when ret<dataLen)
#ifndef IIC_FAKE_COMMANDS
	numBytes = XIic_Send(BADDR_I2C, slaveAddr, pData, dataLen, XIIC_STOP);
#else
	// Don't send I2C but fake numBytes
	numBytes = dataLen;
#endif

	return numBytes;
}

// Reads data from a slave, issues stop after dataLen bytes
// Returns number of bytes sent
int readI2C(u8 slaveAddr, u8* pData, unsigned dataLen)
{
	int numBytes = 0;
#ifndef IIC_FAKE_COMMANDS
	numBytes = XIic_Recv(BADDR_I2C, slaveAddr, pData, dataLen, XIIC_STOP);
#else
	numBytes = dataLen;
#endif

	return numBytes;
}

// For EEPROM random access read
// TODO: Move this to i2c_24c08.[c|h]
// Returns number of bytes sent
int readEEPROM(u8 slaveAddr, u8 addr, u8* pData, unsigned dataLen)
{
	int numBytes;

	// According to datasheet, proper way to do a random access read at
	// given memory address is:
	// * Send device select as write
	// * Write addr byte
	// * Send repeated start
	// * Send device select as read
	// * Read byte (x1) - NOACK
	// * Then normal read, len-1 (as you already got the first byte)

	/*
	numBytes  = XIic_Send(BADDR_I2C, slaveAddr, &addr, 1, XIIC_REPEATED_START);
	numBytes  = XIic_Recv(BADDR_I2C, slaveAddr, pData, 1, XIIC_STOP);
	numBytes += XIic_Recv(BADDR_I2C, slaveAddr, pData+1, dataLen-1, XIIC_STOP);
	*/

	// Great in theory but doesn't work (don't appear to issue stop after 1 byte read)

	// Xilinx simply write the address to it then read, verified working on ML507 with Saleae logic
#ifndef IIC_FAKE_COMMANDS
	XIic_Send(BADDR_I2C, slaveAddr, &addr, 1, XIIC_STOP);
	numBytes = XIic_Recv(BADDR_I2C, slaveAddr, pData, dataLen, XIIC_STOP);
#else
	numBytes = dataLen;
#endif
	return numBytes;
}
