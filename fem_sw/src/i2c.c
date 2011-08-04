/*
 * i2c.c
 *
 * I2C abstraction layer for Xilinx
 *
 */

#include "i2c.h"

/*
 * Performs a write transaction to an I2C slave device.
 * @param slaveAddr I2C slave address
 * @param pData pointer to data buffer to write from
 * @param dataLen length of data (in bytes) to write
 *
 * @return number of bytes written
 */
int writeI2C(u8 slaveAddr, u8* pData, unsigned dataLen)
{
	return XIic_Send(BADDR_I2C, slaveAddr, pData, dataLen, XIIC_STOP);
}

/*
 * Performs a read transaction from an I2C slave device.
 * @param slaveAddr I2C slave address
 * @param pData pointer to data buffer to read to
 * @param dataLen length of data (in bytes) to read
 *
 * @return number of bytes read
 */
int readI2C(u8 slaveAddr, u8* pData, unsigned dataLen)
{
	return XIic_Recv(BADDR_I2C, slaveAddr, pData, dataLen, XIIC_STOP);
}
