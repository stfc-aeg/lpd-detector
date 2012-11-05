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
	u16 header;					//!< Header: Structure header (to identify in EEPROM)

	// Networking (18 bytes)
	u8 net_mac[6];				//!< Networking: MAC address
	u8 net_ip[4];				//!< Networking: IP address
	u8 net_nm[4];				//!< Networking: Netmask
	u8 net_gw[4];				//!< Networking: Default gateway

	// For hardware monitoring (2 bytes)
	u8 temp_high_setpoint;		//!< SysMon: FPGA high (warning) temperature
	u8 temp_crit_setpoint;		//!< SysMon: FPGA critical (shutdown) temperature

	// Versioning information (8 bytes)
	u8 sw_major_version;		//!< Versioning: Software major version
	u8 sw_minor_version;		//!< Versioning: Software minor version
	u8 fw_major_version;		//!< Versioning: Firmware major version
	u8 fw_minor_version;		//!< Versioning: Firmware minor version
	u8 hw_major_version;		//!< Versioning: Hardware major version
	u8 hw_minor_version;		//!< Versioning: Hardware minor version
	u8 board_id;				//!< Versioning: Board ID
	u8 board_type;				//!< Versioning: Board type

	u8 xor_checksum;			//!< Checksum: XOR checksum

};

void createFailsafeConfig(struct fem_config* pConfig);
int readConfigFromEEPROM(unsigned int addr, struct fem_config* pConfig);
int writeConfigToEEPROM(unsigned int addr, struct fem_config* pConfig);

#endif /* FEMCONFIG_H_ */
