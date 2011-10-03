/*
 * femConfig.c
 *
 *  Created on: Aug 3, 2011
 *      Author: mt47
 */

#include "fem.h"
#include "femConfig.h"

// Creates failsafe default config object, used in case EEPROM config is not valid or missing
/*
 * Creates a failsafe FEM configuration structure to be used in case
 * a valid block is not found in EEPROM or for testing.
 *
 * @param pConfig pointer to fem_config to populate
 */
void createFailsafeConfig(struct fem_config* pConfig)
{
	pConfig->header				= CONFIG_MAGIC_WORD;

	// MAC address
	pConfig->net_mac[0]			= 0x00;
	pConfig->net_mac[1]			= 0x0A;
	pConfig->net_mac[2]			= 0x35;
	pConfig->net_mac[3]			= 0x00;
	pConfig->net_mac[4]			= 0xBE;
	pConfig->net_mac[5]			= 0xEF;

	// IP address
	pConfig->net_ip[0]			= 192;
	pConfig->net_ip[1]			= 168;
	pConfig->net_ip[2]			= 0;
	pConfig->net_ip[3]			= 14;

	// Netmask
	pConfig->net_nm[0]			= 255;
	pConfig->net_nm[1]			= 255;
	pConfig->net_nm[2]			= 255;
	pConfig->net_nm[3]			= 0;

	// Default gateway
	pConfig->net_gw[0]			= 192;
	pConfig->net_gw[1]			= 168;
	pConfig->net_gw[2]			= 1;
	pConfig->net_gw[3]			= 1;

	// LM82 setpoints
	pConfig->temp_high_setpoint	= 40;
	pConfig->temp_crit_setpoint	= 75;

	// Software revision
	pConfig->sw_major_version	= 1;
	pConfig->sw_minor_version	= 2;

	// Firmware revision
	pConfig->fw_major_version	= 1;
	pConfig->fw_minor_version	= 0;

	// Hardware revision
	pConfig->hw_major_version	= 1;
	pConfig->hw_minor_version	= 0;

	// Board ID
	pConfig->board_id			= 1;
	pConfig->board_type			= 1;

	// Checksum - not needed for failsafe config
	pConfig->xor_checksum       = 0;

}

/*
 * Reads FEM configuration block to EEPROM starting at addr.
 *
 * @param addr EEPROM start address
 * @param pConfig pointer to fem_config structure to read to
 * @returns 0 on success, -1 on error
 */
int readConfigFromEEPROM(unsigned int addr, struct fem_config* pConfig)
{
	int retVal = 0;
	int readSize;

	readSize = readFromEEPROM(addr, (u8*)pConfig, sizeof(struct fem_config));

	if ( (readSize == sizeof(struct fem_config)) && (pConfig->header == CONFIG_MAGIC_WORD) )
	{

		// Check if checksum field in config is correct
		int byte, byteRange;
		u8 xor_checksum = 0;
		u8* configPtr = (u8*)pConfig;

		// Calculate length of config struct up to but not including trailing checksum
		byteRange = (int)&(pConfig->xor_checksum) - (int)pConfig;

		// Calculate XOR checksum byte-wise
		for (byte = 0; byte < byteRange; byte++) {
			xor_checksum = xor_checksum ^ *configPtr;
			configPtr++;
		}

		// Compare checksum with calculated value
		if (xor_checksum != pConfig->xor_checksum) {
			DBGOUT("ERROR: configuration in EEPROM has incorrect checksum (read 0x%x expected 0x%x)\r\n",
					pConfig->xor_checksum, xor_checksum);
			retVal = -1;
		}
	}
	else
	{
		// Error
		retVal = -1;
	}

	return retVal;
}


/*
 * Writes FEM configuration block to EEPROM starting at addr.
 *
 * @param addr EEPROM start address
 * @param pConfig pointer to fem_config structure to write from
 * @returns 0 on success, -1 on error
 */
int writeConfigToEEPROM(unsigned int addr, struct fem_config* pConfig)
{
	int retVal = 0;
	retVal = writeToEEPROM(0, (u8*)pConfig, sizeof(struct fem_config));
	if ( (retVal == sizeof(struct fem_config)) && (pConfig->header == CONFIG_MAGIC_WORD) )
	{
		// OK
		return 0;
	}
	else
	{
		// Error
		return -1;
	}
}
