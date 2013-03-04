/*
 * sysace.c
 *
 * Wrapper for SystemACE functionality
 *
 */

#include "sysace.h"

/**
 * Triggers the SystemACE controller to reconfigure the chain of JTAG devices.
 * It is assumed that the SystemACE controller is already initialised.
 * @param pAce pointer to XSysAce device
 * @param idx index of image to use (must be 0-7)
 */
void reloadChain(XSysAce *pAce, unsigned int idx)
{
	// Configure SystemACE to reload specified image on reset, then assert reset
	XSysAce_SetCfgAddr(pAce, idx);
	XSysAce_SetStartMode(pAce, FALSE, TRUE);
	XSysAce_ResetCfg(pAce);
}

/**
 * Writes a data buffer containing a SystemACE image to the Compact Flash card
 * @param idx index of image to write between 1-7, 0 is reserved as a failsafe boot image
 * @param addr base address in DDR of sysace image
 * @param len length of sysace image in bytes
 *
 * @return 0 for success, -1 for failure
 */
int writeImage(unsigned int idx, u32 addr, u32 len)
{
	char fname[] = "a:\\Ver_1\\revX\\revX.ace";
	void *pHandle;
	int retVal;

	// Sanitise idx
	if (idx>7 || idx==0)
	{
		return -1;
	}

	// Insert sysace image number into path and filename
	fname[12] = (char)(48+idx);
	fname[17] = (char)(48+idx);

	// Dump filename
	// TODO: SYSTEMACE: Remove DBGOUT once verified OK
	DBGOUT("SystemACE filename (idx=%d): '", idx);
	DBGOUT(fname);
	DBGOUT("'\r\n");

	// Open file for writing (w option discards any existing file, or creates it if not present)
	pHandle = sysace_fopen(fname, "w");
	if (pHandle==NULL)
	{
		DBGOUT("SysACE: Cannot open file '");
		DBGOUT(fname);
		DBGOUT("' for writing!\r\n");
		return -1;
	}

	// Write data to file
	retVal = sysace_fwrite((void*)addr, 1, len, pHandle);
	if (retVal==-1)
	{
		DBGOUT("SysACE: Error writing data to file\r\n");
		sysace_fclose(pHandle);
		return -1;
	}

	// Close file (flush data to disk), exit
	retVal = sysace_fclose(pHandle);
	return retVal;
}

/**
 * My copy of the xsysace self test routine with extra debug
 * @param InstancePtr pointer to XSysAce
 *
 * @return operation status
 */
int mySelfTest(XSysAce *InstancePtr)
{
	int Result;

	// TODO: SYSTEMACE: Remove this function once SystemAce working OK

	// THIS CODE IS ADDED TO ORIGINAL XSYSACE_SELFTEST AS DIAGS!
/*
	int status;
	status = (XSysAce_GetStatusReg(InstancePtr->BaseAddress));// & XSA_SR_CFGLOCK_MASK);
	DBGOUT("hurfDurf: SystemACE status is 0x%x\r\n",status);
	status = XSysAce_Lock(InstancePtr, TRUE);
	DBGOUT("hurfDurf: Trying to lock SystemACE... ");
	if (status!=XST_SUCCESS) { DBGOUT("failed.\r\n"); } else { DBGOUT("OK!\r\n"); }
	if (XSysAce_IsMpuLocked(InstancePtr->BaseAddress)) {
		DBGOUT("SA_selfTest: SystemACE lock is ENABLED\r\n");
	} else {
		DBGOUT("SA_selfTest: SystemACE lock is DISABLED\r\n");
	}
*/

	Xil_AssertNonvoid(InstancePtr != NULL);
	Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

	/*
	 * Grab a lock (expect immediate success)
	 */
	Result = XSysAce_Lock(InstancePtr, TRUE);
	if (Result != XST_SUCCESS) {
		DBGOUT("SA_selfTest: failed at lock (%d)\r\n", Result);
		return Result;
	}

	/*
	 * Verify the lock was retrieved
	 */
	if (!XSysAce_IsMpuLocked(InstancePtr->BaseAddress)) {
		DBGOUT("SA_selfTest: failed at lock verify\r\n");
		return XST_FAILURE;
	}

	/*
	 * Release the lock
	 */
	XSysAce_Unlock(InstancePtr);

	/*
	 * Verify the lock was released
	 */
	if (XSysAce_IsMpuLocked(InstancePtr->BaseAddress)) {
		DBGOUT("SA_selfTest: failed at lock release\r\n");
		return XST_FAILURE;
	}

	/*
	 * If there are currently any errors on the device, fail self-test
	 */
	if (XSysAce_GetErrorReg(InstancePtr->BaseAddress) != 0) {
		DBGOUT("SA_selfTest: ErrorReg: 0x%x\r\n", XSysAce_GetErrorReg(InstancePtr->BaseAddress));
		return XST_FAILURE;
	}

	return XST_SUCCESS;
}
