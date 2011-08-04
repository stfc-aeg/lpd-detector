/*
 * femConfig.h
 *
 *  Created on: Aug 3, 2011
 *      Author: mt47
 */

#ifndef FEMCONFIG_H_
#define FEMCONFIG_H_

#include "i2c_24c08.h"
#include "xil_types.h"

// Header for config structure, verified before it is used to configure FEM
#define CONFIG_MAGIC_WORD			0xFACE

// Struct for storage of FEM parameters (normally kept in EEPROM)
struct fem_config
{
	// Header (2 bytes)
	u16 header;

	// Networking (18 bytes)
	u8 net_mac[6];
	u8 net_ip[4];
	u8 net_nm[4];
	u8 net_gw[4];

	// For hardware monitoring (2 bytes)
	u8 temp_high_setpoint;
	u8 temp_crit_setpoint;

	// Versioning information (8 bytes)
	u8 sw_major_version;
	u8 sw_minor_version;
	u8 fw_major_version;
	u8 fw_minor_version;
	u8 hw_major_version;
	u8 hw_minor_version;
	u8 board_id;
	u8 board_type;

	u8 xor_checksum;

};

void createFailsafeConfig(struct fem_config* pConfig);
int readConfigFromEEPROM(unsigned int addr, struct fem_config* pConfig);
int writeConfigToEEPROM(unsigned int addr, struct fem_config* pConfig);

#endif /* FEMCONFIG_H_ */
