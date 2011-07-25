/*
 * i2c_24c08.h
 *
 * Support functions for M24C08 I2C device
 *
 * --------------------------------------------------------
 *
 * Device:     M24C08
 * I2C addr:   0x50
 *
 * 8k EEPROM, 16 byte page, 512 pages
 *
 */

#ifndef I2C_24C08_H_
#define I2C_24C08_H_

#include "xparameters.h"
#include "fem.h"
#include "i2c.h"
#include "sleep.h"
#include <stdio.h>
#include <string.h>

// Slave address
#define IIC_ADDRESS_EEPROM		0x50

// M24C08 parameters
#define EEPROM_PAGE_SIZE		16
#define EEPROM_NUM_PAGES		512

// Write delay between pages in ms at 100kHz mode taken from datasheet
// (We could poll ACK to see when writes are completed but we just wait the maximum possible write time instead!)
#define EEPROM_WRITE_DELAY_MS	5

int readFromEEPROM(unsigned int addr, u8* pData, unsigned int len);
int writeToEEPROM(unsigned int addr, u8* pData, unsigned int len);

int readConfigFromEEPROM(unsigned int addr, struct fem_config* pConfig);
int writeConfigToEEPROM(unsigned int addr, struct fem_config* pConfig);

#endif /* I2C_24C08_H_ */
