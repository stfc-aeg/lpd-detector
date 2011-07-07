/*
 * i2c.h
 *
 *  Created on: 29 Mar 2011
 *      Author: mt47
 *
 * Xilinx platform wrapper for I2C subsystem
 */

#ifndef I2C_H_
#define I2C_H_

#include "xparameters.h"
#include "fem.h"
#include "xiic.h"
#include <stdio.h>

//#define IIC_FAKE_COMMANDS		// Uncomment to fake I2C operations

int writeI2C(u8 slaveAddr, u8* pData, unsigned dataLen);
int readI2C(u8 slaveAddr, u8* pData, unsigned dataLen);
int readEEPROM(u8 slaveAddr, u8 addr, u8* pData, unsigned dataLen);

#endif /* I2C_H_ */
