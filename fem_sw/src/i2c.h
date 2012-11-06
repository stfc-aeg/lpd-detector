/**
 * @file i2c.h
 * @author Matt Thorpe, STFC Application Engineering Group
 *
 * Top level I2C abstraction layer.  Wrapper for Xilinx I2C libraries.
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
enum i2c_opTypes
{
	IIC_OPERATION_READ  = 1,
	IIC_OPERATION_WRITE = 2
};

//! I2C controller indexes
enum i2c_controllerIdx
{
	IIC_IDX_LM82		= 0,
	IIC_IDX_EEPROM		= 1,
	IIC_IDX_PWR_RHS		= 2,
	IIC_IDX_PWR_LHS		= 3
};

//! I2C error codes
enum i2c_errors
{
	IIC_ERR_INVALID_INDEX		= -1,
	IIC_ERR_SLAVE_NACK			= -2,
	IIC_ERR_TIMEOUT				= -3,
	IIC_ERR_BUS_BUSY			= -4,
	IIC_ERR_SET_ADDR			= -5,
	IIC_ERR_INVALID_OP_MODE		= -6,
	IIC_ERR_GENERAL_CALL_ADDR	= -7,
	IIC_ERR_LAST				= -8
};

// I2C management functions
int initI2C(void);
int startI2C(void);
int stopI2C(void);
void resetI2C(void);

// I2C ISRs
static void statusHandler(XIic* pIic, int event);		//!< I2C status change ISR
static void sendHandler(XIic* pIic, int byteCount);		//!< I2C send ISR
static void recvHandler(XIic* pIic, int byteCount);		//!< I2C receive ISR

// I2C operations
int writeI2C(int interfaceIdx, u8 slaveAddr, u8* pData, unsigned dataLen);
int readI2C(int interfaceIdx, u8 slaveAddr, u8* pData, unsigned dataLen);

// I2C main handler (called by read / write functions)
int doI2COperation(int interfaceIdx, int opMode, u8 slaveAddr, u8* pData, unsigned dataLen);

XIic iicLm82;		//!< XIic handler for LM82 I2C bus
XIic iicEeprom;		//!< XIic handler for EEPROM I2C bus
XIic iicLhs;		//!< XIic handler for PWR_LHS I2C bus
XIic iicRhs;		//!< XIic handler for PWR_RHS I2C bus

// Flags used by interrupt handlers
static volatile int iicInstanceIdx;		//!< Current controller index (i2c_controllerIdx)
static volatile int sendComplete;		//!< Flag denotes if current write operation is complete
static volatile int recvComplete;		//!< Flag denotes if current read operation is complete
static volatile int busNotBusy;			//!< Bus busy flag
static volatile int slaveNoAck;			//!< Slave NACK
static volatile int iicError;			//!< Contains i2c error code (if non zero)
static volatile int numBytesRemaining;	//!< Count of bytes remaining in operation

#endif /* I2C_H_ */
