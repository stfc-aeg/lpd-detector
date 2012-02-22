/*
 * i2c_lm82.h
 *
 *  Created on: 1 Apr 2011
 *      Author: mt47
 *
 * Support functions for LM82 I2C device
 *
 * --------------------------------------------------------
 *
 * I2C Device: LM82
 * Address:    0x18
 *
 * Local / Remote 8-bit temperature monitoring system
 * with INT and T_CRIT_A interrupt outputs.
 * INT is triggered if a temp exceeds HIGH SP
 * T_CRIT_A is triggered if a temp exceeds T_CRIT SP
 *
 * Local then remote temp is converted, takes ~480ms for cycle
 *
 * LM82 power on state:
 *
 * Command register	= 0
 * Status register	= 0
 * Configuration rg = 0
 * Local temp		= 0c
 * Remote temp. 	= 0c
 * Local T_CRIT		= 127c
 * Remote T_CRIT	= 127c
 * INT and T_CRIT_A enabled
 *
 */

#ifndef I2C_LM82_H_
#define I2C_LM82_H_

#include "xparameters.h"
#include "fem.h"
#include "i2c.h"
#include <stdio.h>

// Slave address
#define IIC_ADDRESS_TEMP				0x18

// LM82 registers
#define LM82_REG_READ_LOCAL_TEMP		0x00
#define LM82_REG_READ_REMOTE_TEMP		0x01
#define LM82_REG_READ_STATUS			0x02
#define LM82_REG_READ_CONFIG			0x03
#define LM82_REG_READ_LOCAL_SP			0x05	// SP == SetPoint
#define LM82_REG_READ_REMOTE_SP			0x07
#define LM82_REG_WRITE_CONFIG			0x09
#define LM82_REG_WRITE_LOCAL_SP			0x0B
#define LM82_REG_WRITE_REMOTE_SP		0x0D
#define LM82_REG_READ_TCRIT_SP			0x42
#define LM82_REG_WRITE_TCRIT_SP			0x5A

// LM82 status bits (LM82_REG_READ_STATUS)
#define LM82_STATUS_LOCAL_CRIT			(1<<0)
#define LM82_STATUS_REMOTE_CRIT			(1<<1)
#define LM82_STATUS_LOCAL_HIGH			(1<<6)
#define LM82_STATUS_REMOTE_HIGH			(1<<4)
#define LM82_STATUS_REMOTE_DISCONNECT	(1<<2)

// Overheat temperature (interrupt generated to Spartan config FPGA)
#define LM82_HIGH_TEMP					70

// Critical temperature (hard power shutdown)
#define LM82_CRIT_TEMP					80

// ----------------------------------------------------------------------------

void initLM82(int highTemp, int critTemp);
u8 readStatus(void);
int readTemp(u8 tempRegCmd);
int readLocalTemp(void);
int readRemoteTemp(void);
int convertTemperature(u8 rawVal);

#endif /* I2C_LM82_H_ */
