/*
 * i2c_24c08.c
 *
 * Support functions for M24C08 I2C device
 *
 */

#include "i2c_24c08.h"

/**
 * Reads a number of bytes from a generic 24cXX EEPROM device
 * @param slaveAddr I2C address of slave EEPROM
 * @param addr address offset of EEPROM
 * @param pData pointer to data buffer to fill
 * @param len number of bytes to read
 *
 * @return number of bytes read
 */
int readEEPROM(u8 slaveAddr, u8 addr, u8* pData, unsigned len)
{
	int numBytes = 0;

	// Send EEPROM read request to $addr
	numBytes = writeI2C(IIC_IDX_EEPROM, slaveAddr, &addr, 1);
	if (numBytes!=1) { return numBytes; }

	// Do read operation
	return readI2C(IIC_IDX_EEPROM, slaveAddr, pData, len);
}


/**
 * Reads data from the M24C08 8K EEPROM on the FEM / development board
 * @param addr address offset of EEPROM
 * @param pData pointer to data buffer to fill
 * @param len number of bytes to read
 *
 * @return number of bytes read
 */
int readFromEEPROM(unsigned int addr, u8* pData, unsigned int len)
{
	return readEEPROM(IIC_ADDRESS_EEPROM, addr, pData, len);
}


/**
 * Writes data to the M24C08 8K EEPROM on the FEM / development board
 * @param addr address offset of EEPROM
 * @param pData pointer to data buffer to write from
 * @param len number of bytes to write
 *
 * @return number of bytes written
 */
int writeToEEPROM(unsigned int addr, u8* pData, unsigned int len)
{
	int firstPage, lastPage, page, firstWriteSize, lastWriteSize, currentAddr;
	int totalBytes = 0;
	int numBytes = 0;
	u8 buffer[EEPROM_PAGE_SIZE + 1];

	// First byte of any write is address
	currentAddr = addr;
	buffer[0] = currentAddr;

	// Determine if write spans more than one page
	firstPage = addr / EEPROM_PAGE_SIZE;
	lastPage = (addr + (len-1)) / EEPROM_PAGE_SIZE;

	// DELAY
	usleep(EEPROM_WRITE_DELAY_MS*1000);

	if (firstPage != lastPage)		// Write spans pages
	{
		// Determine first write size
		firstWriteSize = EEPROM_PAGE_SIZE - (addr%EEPROM_PAGE_SIZE);

		// Determine last write size
		lastWriteSize = (len-firstWriteSize)%EEPROM_PAGE_SIZE;
		if (lastWriteSize==0) {
			lastWriteSize = EEPROM_PAGE_SIZE;
		}

		// First page
		memcpy( &buffer[1], pData, firstWriteSize );
		numBytes = writeI2C( IIC_IDX_EEPROM, IIC_ADDRESS_EEPROM, buffer, firstWriteSize+1 );
		if (numBytes < 0)
		{
			return numBytes;
		}
		else
		{
			totalBytes += numBytes;
		}
		currentAddr += firstWriteSize;
		buffer[0] = currentAddr;

		// Middle whole pages, if necessary
		for (page=(firstPage+1); page<=(lastPage-1); page++)
		{
			usleep(EEPROM_WRITE_DELAY_MS*1000);
			memcpy( &buffer[1], pData+(currentAddr-addr), EEPROM_PAGE_SIZE );
			numBytes = writeI2C( IIC_IDX_EEPROM, IIC_ADDRESS_EEPROM, buffer, EEPROM_PAGE_SIZE+1 );
			if (numBytes < 0)
			{
				return numBytes;
			}
			else
			{
				totalBytes += numBytes;
			}
			currentAddr += EEPROM_PAGE_SIZE;
			buffer[0] = currentAddr;
		}

		// Last page
		usleep(EEPROM_WRITE_DELAY_MS*1000);
		memcpy( &buffer[1], pData+(currentAddr-addr), lastWriteSize );
		numBytes = writeI2C( IIC_IDX_EEPROM, IIC_ADDRESS_EEPROM, buffer, lastWriteSize+1 );
		if (numBytes < 0)
		{
			return numBytes;
		}
		else
		{
			totalBytes += numBytes;
		}

		return totalBytes;

	} else {			// Write is to single page only
		memcpy( &buffer[1], pData, len);
		usleep(EEPROM_WRITE_DELAY_MS*1000);
		return writeI2C(IIC_IDX_EEPROM, IIC_ADDRESS_EEPROM, buffer, len + 1);
	}
}
