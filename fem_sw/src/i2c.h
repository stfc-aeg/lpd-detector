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
#include "xiic.h"
#include "xtime_l.h"
#include <stdio.h>

//! I2C operation types
#define IIC_OPERATION_READ		1
#define IIC_OPERATION_WRITE		2

//! I2C controller indexes
#define IIC_IDX_LM82			0
#define IIC_IDX_EEPROM			1
#define IIC_IDX_PWR_RHS			2
#define IIC_IDX_PWR_LHS			3

// I2C management functions
int initI2C(void);
int startI2C(void);
int stopI2C(void);
void resetI2C(void);

// I2C ISRs
static void statusHandler(XIic* pIic, int event);
static void sendHandler(XIic* pIic, int byteCount);
static void recvHandler(XIic* pIic, int byteCount);

// I2C operations
int writeI2C(int interfaceIdx, u8 slaveAddr, u8* pData, unsigned dataLen);
int readI2C(int interfaceIdx, u8 slaveAddr, u8* pData, unsigned dataLen);

// I2C main handler (called by read / write functions)
int doI2COperation(int interfaceIdx, int opMode, u8 slaveAddr, u8* pData, unsigned dataLen);

// XIic instances
XIic iicLm82, iicEeprom, iicLhs, iicRhs;

// Flags used by interrupt handlers
static volatile int iicInstanceIdx, sendComplete, recvComplete, busNotBusy, slaveNoAck, iicError;
static volatile int numBytes;
static XIic* pIic;

#endif /* I2C_H_ */
