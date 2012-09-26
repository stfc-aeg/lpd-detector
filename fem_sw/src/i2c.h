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

//! I2C error codes
#define IIC_ERR_INVALID_INDEX		-1
#define IIC_ERR_SLAVE_NACK			-2
#define IIC_ERR_TIMEOUT				-3
#define IIC_ERR_BUS_BUSY			-4
#define IIC_ERR_SET_ADDR			-5
#define IIC_ERR_INVALID_OP_MODE		-6
#define IIC_ERR_GENERAL_CALL_ADDR	-7

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
static volatile int iicInstanceIdx, sendComplete, recvComplete, busNotBusy, slaveNoAck, iicError, numBytesRemaining;

#endif /* I2C_H_ */
