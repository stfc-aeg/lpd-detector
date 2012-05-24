/*
 * i2c.c
 *
 * I2C abstraction layer for Xilinx
 *
 */

#include "i2c.h"

/**
 * Performs a write transaction to an I2C slave device.
 * @param slaveAddr I2C slave address
 * @param pData pointer to data buffer to write from
 * @param dataLen length of data (in bytes) to write
 * @param bAddr hardware base address of I2C controller to use
 *
 * @return number of bytes written
 */
int writeI2C(u32 bAddr, u8 slaveAddr, u8* pData, unsigned dataLen)
{
	if (dataLen == 0) return 0;
	return XIic_Send(bAddr, slaveAddr, pData, dataLen, XIIC_STOP);
}

/**
 * Performs a read transaction from an I2C slave device.
 * @param slaveAddr I2C slave address
 * @param pData pointer to data buffer to read to
 * @param dataLen length of data (in bytes) to read
 * @param bAddr hardware base address of I2C controller to use
 *
 * @return number of bytes read
 */
int readI2C(u32 bAddr, u8 slaveAddr, u8* pData, unsigned dataLen)
{
	if (dataLen == 0) return 0;
	return XIic_Recv(bAddr, slaveAddr, pData, dataLen, XIIC_STOP);
}
