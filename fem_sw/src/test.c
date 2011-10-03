/*
 * test.c
 *
 *  Created on: Aug 3, 2011
 *      Author: mt47
 */

#include "test.h"
#include "rdma.h"

/*
 * Test routine for various hardware components
 * @param bitmask an 8-bit bitmask that controls which tests are run
 *
 * @return 0 on pass, -1 on fail
 */
int testThread(u8 bitmask)
{

	DBGOUT("Test: Entered test function!\r\n");

	/*
	// *** For LM82 tests ***
	int localTemp = 0;
	int remoteTemp = 0;
	u8 cmd = LM82_REG_READ_STATUS;
	u8 stat = 0;
	*/

	// *** For EEPROM tests ***
/*
	int i;
	u8 readBuffer[8192];
	u8 dummyData[] = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,
					  16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,
					  32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,
					  48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63};

	// Test patterns for EEPROM write
	u8 blankData[] = {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF};
	//u8 blankData[] = {0xA5,0x5A,0xA5,0x5A,0xA5,0x5A,0xA5,0x5A,0xA5,0x5A,0xA5,0x5A,0xA5,0x5A,0xA5,0x5A};
	//u8 blankData[] = {0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F};
*/

	// Initalise LM82 device with setpoints we can easily trigger
	//DBGOUT("TEST: Configuring LM82 device... ");
	//initLM82(29,32);		// (warn temp, crit temp)
	//DBGOUT("OK!\r\n");

	// ------------------------------------------------------------------------
	// LM82 tester
	/*
	while (1)
	{
		sleep(10000);
		remoteTemp = readRemoteTemp();
		localTemp = readLocalTemp();
		writeI2C(IIC_ADDRESS_TEMP, &cmd, 1);
		readI2C(IIC_ADDRESS_TEMP, &stat, 1);
		DBGOUT("Test:  Local LM82 temp: %dc\r\n", localTemp);
		DBGOUT("Test: Remote LM82 temp: %dc\r\n", remoteTemp);
		DBGOUT("Test:  Status register: 0x%x\r\n", stat);
	}
	*/

	// ------------------------------------------------------------------------
	// EEPROM tester

	/*
	usleep(2000);

	// Blank out first 8 pages for testing
	for (i=0; i<8; i++)
	{
		writeToEEPROM((i*16), blankData, 16);
	}

	// Do test write
	writeToEEPROM(7, dummyData, 34);

	// Do readback to check data
	DBGOUT("----------------------\r\n");
	readFromEEPROM(0, readBuffer, 8192);
	for (i=0; i<16; i++)
	{
		// sooo ugly :(
		if (i==0) { DBGOUT("00"); }
		DBGOUT("%x: %x %x %x %x %x %x %x %x   %x %x %x %x %x %x %x %x \r\n",
			(i*16)*16, readBuffer[(i*16)+0], readBuffer[(i*16)+1], readBuffer[(i*16)+2], readBuffer[(i*16)+3], readBuffer[(i*16)+4], readBuffer[(i*16)+5], readBuffer[(i*16)+6], readBuffer[(i*16)+7],
			readBuffer[(i*16)+8], readBuffer[(i*16)+9], readBuffer[(i*16)+10], readBuffer[(i*16)+11], readBuffer[(i*16)+12], readBuffer[(i*16)+13], readBuffer[(i*16)+14], readBuffer[(i*16)+15] );
	}
	*/

	// ------------------------------------------------------------------------
	// Rob RDMA / RS232 link test

	// ***********************
	// Only for RDMA2 library!
	// ***********************
	int status;

	DBGOUT("Test: Running old RDMA tests...\r\n");
	u32 addr;
	u32 regVal = 0;

	// Read read-only register
	addr = 4;
	regVal = readRdma(addr);
	DBGOUT("Test: RO:RDMA register 0x%x = 0x%x\r\n", addr, regVal);

	// Read read-write register
	addr = 1;
	regVal = readRdma(addr);
	DBGOUT("Test: RW:RDMA register 0x%x = 0x%x\r\n", addr, regVal);

	// Write read-write register
	u32 testValue = 0xDEADBEEF;
	writeRdma(addr, testValue);
	DBGOUT("Test: Wrote 0x%x to 0x%x\r\n", testValue, addr);

	// Read read-write register
	regVal = readRdma(addr);
	DBGOUT("Test: RW:RDMA register 0x%x = 0x%x\r\n", addr, regVal);

	// Don't let EEPROM tests run!
	return 0;

	// ------------------------------------------------------------------------
	// FEM configuration struct test
	/*
	DBGOUT("TEST: Running EEPROM struct test...\r\n");
	struct fem_config cfg;		// Used to write to EEPROM
	struct fem_config test;		// Read back from EEPROM

	// Make a dummy struct
	createFailsafeConfig(&cfg);

	// Write to EEPROM
	DBGOUT("TEST: Writing EEPROM struct...\r\n");
	writeToEEPROM(0, (u8*)&cfg, sizeof(struct fem_config));

	// Read back
	DBGOUT("TEST: Reading EEPROM struct...\r\n");
	readFromEEPROM(0, (u8*) &test, sizeof(struct fem_config));

	// Test values
	// NOTE: THIS DOES NOT TEST ALL PARAMS!
	int numErrors = 0;
	if (test.net_mac[0] != cfg.net_mac[0]) { DBGOUT("EEPROM: mac_address[0] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[0], test.net_mac[0]); numErrors++; }
	if (test.net_mac[1] != cfg.net_mac[1]) { DBGOUT("EEPROM: mac_address[1] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[1], test.net_mac[1]); numErrors++; }
	if (test.net_mac[2] != cfg.net_mac[2]) { DBGOUT("EEPROM: mac_address[2] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[2], test.net_mac[2]); numErrors++; }
	if (test.net_mac[3] != cfg.net_mac[3]) { DBGOUT("EEPROM: mac_address[3] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[3], test.net_mac[3]); numErrors++; }
	if (test.net_mac[4] != cfg.net_mac[4]) { DBGOUT("EEPROM: mac_address[4] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[4], test.net_mac[4]); numErrors++; }
	if (test.net_mac[5] != cfg.net_mac[5]) { DBGOUT("EEPROM: mac_address[5] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[5], test.net_mac[5]); numErrors++; }
	if (test.temp_high_setpoint != cfg.temp_high_setpoint) { DBGOUT("EEPROM: temp_high_setpoint differs! (Should be 0x%x, got 0x%x)\r\n", cfg.temp_high_setpoint, test.temp_high_setpoint); numErrors++; }
	if (test.temp_crit_setpoint != cfg.temp_crit_setpoint) { DBGOUT("EEPROM: temp_crit_setpoint differs! (Should be 0x%x, got 0x%x)\r\n", cfg.temp_crit_setpoint, test.temp_crit_setpoint); numErrors++; }
	if (test.sw_major_version != cfg.sw_major_version) { DBGOUT("EEPROM: sw_major_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.sw_major_version, test.sw_major_version); numErrors++; }
	if (test.sw_minor_version != cfg.sw_minor_version) { DBGOUT("EEPROM: sw_minor_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.sw_minor_version, test.sw_minor_version); numErrors++; }
	if (test.fw_major_version != cfg.fw_major_version) { DBGOUT("EEPROM: fw_major_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.fw_major_version, test.fw_major_version); numErrors++; }
	if (test.fw_minor_version != cfg.fw_minor_version) { DBGOUT("EEPROM: fw_minor_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.fw_minor_version, test.fw_minor_version); numErrors++; }
	if (test.hw_major_version != cfg.hw_major_version) { DBGOUT("EEPROM: hw_major_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.hw_major_version, test.hw_major_version); numErrors++; }
	if (test.hw_minor_version != cfg.hw_minor_version) { DBGOUT("EEPROM: hw_minor_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.hw_minor_version, test.hw_minor_version); numErrors++; }
	if (test.board_id != cfg.board_id) { DBGOUT("EEPROM: board_id differs! (Should be 0x%x, got 0x%x)\r\n", cfg.board_id, test.board_id); numErrors++; }
	if (test.board_type != cfg.board_type) { DBGOUT("EEPROM: board_id differs! (Should be 0x%x, got 0x%x)\r\n", cfg.board_type, test.board_type); numErrors++; }
	if (numErrors >0 )
	{
		DBGOUT("TEST: EEPROM struct readback encountered %d error(s)\r\n", numErrors);
	}
	else
	{
		DBGOUT("TEST: EEPROM struct readback test OK!\r\n");
	}
	*/
	// Do readback to check data
	/*
	 u8 readBuffer[sizeof(struct fem_config)];
	int i;
	readFromEEPROM(0, readBuffer, sizeof(struct fem_config));
	DBGOUT("----------------------\r\n");
	for (i=0; i<16; i++)
	{
		// sooo ugly :(
		if (i==0) { DBGOUT("00"); }
		DBGOUT("%x: %x %x %x %x %x %x %x %x   %x %x %x %x %x %x %x %x \r\n",
			(i*16)*16, readBuffer[(i*16)+0], readBuffer[(i*16)+1], readBuffer[(i*16)+2], readBuffer[(i*16)+3], readBuffer[(i*16)+4], readBuffer[(i*16)+5], readBuffer[(i*16)+6], readBuffer[(i*16)+7],
			readBuffer[(i*16)+8], readBuffer[(i*16)+9], readBuffer[(i*16)+10], readBuffer[(i*16)+11], readBuffer[(i*16)+12], readBuffer[(i*16)+13], readBuffer[(i*16)+14], readBuffer[(i*16)+15] );
	}
	 */
	DBGOUT("Test: Thread exiting.\r\n");

	return 0;
}
