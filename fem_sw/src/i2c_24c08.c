/*
 * i2c_24c08.c
 *
 * Support functions for M24C08 I2C device
 *
 */

#include "i2c_24c08.h"

// For EEPROM random access read
// Returns number of bytes sent
int readEEPROM(u8 slaveAddr, u8 addr, u8* pData, unsigned dataLen)
{
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
	XIic_Send(BADDR_I2C, slaveAddr, &addr, 1, XIIC_STOP);
	return XIic_Recv(BADDR_I2C, slaveAddr, pData, dataLen, XIIC_STOP);

}

// Reads data from EEPROM
int readFromEEPROM(unsigned int addr, u8* pData, unsigned int len)
{

	return readEEPROM(IIC_ADDRESS_EEPROM, addr, pData, len);
}

// Writes data to EEPROM
int writeToEEPROM(unsigned int addr, u8* pData, unsigned int len)
{
	int firstPage, lastPage, page, firstWriteSize, lastWriteSize, totalBytes, currentAddr;
	u8 buffer[EEPROM_PAGE_SIZE + 1];

	// First byte of any write is address
	currentAddr = addr;
	buffer[0] = currentAddr;

	// Determine if write spans more than one page
	firstPage = addr / EEPROM_PAGE_SIZE;
	lastPage = (addr + (len-1)) / EEPROM_PAGE_SIZE;

	// DELAY
	usleep(EEPROM_WRITE_DELAY_MS*1000);

	if (firstPage != lastPage)
	{
		// Write spans pages

		// Determine first write size
		firstWriteSize = EEPROM_PAGE_SIZE - (addr%EEPROM_PAGE_SIZE);

		// Determine last write size
		lastWriteSize = (len-firstWriteSize)%EEPROM_PAGE_SIZE;
		if (lastWriteSize==0) {
			lastWriteSize = EEPROM_PAGE_SIZE;
		}

		// First page
		memcpy( &buffer[1], pData, firstWriteSize );
		totalBytes += writeI2C( IIC_ADDRESS_EEPROM, buffer, firstWriteSize+1 );
		currentAddr += firstWriteSize;
		buffer[0] = currentAddr;

		// Middle whole pages, if necessary
		for (page=(firstPage+1); page<=(lastPage-1); page++)
		{
			// DELAY
			usleep(EEPROM_WRITE_DELAY_MS*1000);
			memcpy( &buffer[1], pData+(currentAddr-addr), EEPROM_PAGE_SIZE );
			totalBytes += writeI2C( IIC_ADDRESS_EEPROM, buffer, EEPROM_PAGE_SIZE+1 );
			currentAddr += EEPROM_PAGE_SIZE;
			buffer[0] = currentAddr;
		}

		// Last page
		// DELAY
		usleep(EEPROM_WRITE_DELAY_MS*1000);
		memcpy( &buffer[1], pData+(currentAddr-addr), lastWriteSize );
		totalBytes += writeI2C( IIC_ADDRESS_EEPROM, buffer, lastWriteSize+1 );

		return totalBytes;

	} else {
		// Write is to single page only

		memcpy( &buffer[1], pData, len);
		// DELAY
		usleep(EEPROM_WRITE_DELAY_MS*1000);
		return writeI2C(IIC_ADDRESS_EEPROM, buffer, len + 1);
	}
}
