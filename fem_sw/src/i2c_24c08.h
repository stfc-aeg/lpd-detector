/**
 * @file i2c_24c08.h
 * @author Matt Thorpe, STFC Application Engineering Group
 *
 * Support library for M24C08 I2C EEPROM device
 *
 */

#ifndef I2C_24C08_H_
#define I2C_24C08_H_

#include "xparameters.h"
#include "femConfig.h"
#include "i2c.h"
#ifdef __PPC__
#include "sleep.h"
#else
#include "calib_sleep.h"
#endif
#include <stdio.h>
#include <string.h>

#define IIC_ADDRESS_EEPROM		0x50	//!< Slave address of EEPROM
#define EEPROM_PAGE_SIZE		16		//!< Page size of EEPROM
#define EEPROM_NUM_PAGES		512		//!< Number of pages in EEPROM
#define EEPROM_WRITE_DELAY_MS	5		//!< Write delay between pages (ms) at 100kHz mode

int readEEPROM(u8 slaveAddr, u8 addr, u8* pData, unsigned len);
int readFromEEPROM(unsigned int addr, u8* pData, unsigned int len);
int writeToEEPROM(unsigned int addr, u8* pData, unsigned int len);

#endif /* I2C_24C08_H_ */
