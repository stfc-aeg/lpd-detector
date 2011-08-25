/*
 * i2c_24c08.c
 *
 * Support functions for M24C08 I2C device
 *
 */

#include "i2c_24c08.h"

/*
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
	XIic_Send(BADDR_I2C_EEPROM, slaveAddr, &addr, 1, XIIC_STOP);
	return XIic_Recv(BADDR_I2C_EEPROM, slaveAddr, pData, len, XIIC_STOP);

}

/*
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

/*
 * Writes data to the M24C08 8K EEPROM on the FEM / development board
 * @param addr address offset of EEPROM
 * @param pData pointer to data buffer to write from
 * @param len number of bytes to write
 *
 * @return number of bytes written
 */
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
		totalBytes += writeI2C( BADDR_I2C_EEPROM, IIC_ADDRESS_EEPROM, buffer, firstWriteSize+1 );
		currentAddr += firstWriteSize;
		buffer[0] = currentAddr;

		// Middle whole pages, if necessary
		for (page=(firstPage+1); page<=(lastPage-1); page++)
		{
			// DELAY
			usleep(EEPROM_WRITE_DELAY_MS*1000);
			memcpy( &buffer[1], pData+(currentAddr-addr), EEPROM_PAGE_SIZE );
			totalBytes += writeI2C( BADDR_I2C_EEPROM, IIC_ADDRESS_EEPROM, buffer, EEPROM_PAGE_SIZE+1 );
			currentAddr += EEPROM_PAGE_SIZE;
			buffer[0] = currentAddr;
		}

		// Last page
		// DELAY
		usleep(EEPROM_WRITE_DELAY_MS*1000);
		memcpy( &buffer[1], pData+(currentAddr-addr), lastWriteSize );
		totalBytes += writeI2C( BADDR_I2C_EEPROM, IIC_ADDRESS_EEPROM, buffer, lastWriteSize+1 );

		return totalBytes;

	} else {
		// Write is to single page only

		memcpy( &buffer[1], pData, len);
		// DELAY
		usleep(EEPROM_WRITE_DELAY_MS*1000);
		return writeI2C(BADDR_I2C_EEPROM, IIC_ADDRESS_EEPROM, buffer, len + 1);
	}
}
