/*
 * i2c.h
 *
 *  Created on: 29 Mar 2011
 *      Author: mt47
 *
 * I2C abstraction layer for Xilinx
 *
 */

#ifndef I2C_H_
#define I2C_H_

#include "xparameters.h"
#include "fem.h"
#include "xiic_l.h"
#include <stdio.h>

int writeI2C(u32 bAddr, u8 slaveAddr, u8* pData, unsigned dataLen);
int readI2C(u32 bAddr, u8 slaveAddr, u8* pData, unsigned dataLen);

#endif /* I2C_H_ */
