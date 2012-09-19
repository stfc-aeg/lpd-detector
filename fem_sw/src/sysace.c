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
 * Deletes the configuration image
 * @param idx index of image to delete (0-7)
 * @return 0 for success, -1 for failure
 */
int deleteImage(unsigned int idx)
{
	// Can we do this with xilfatfs??
	return 42;
}

/*
 * Writes a data buffer to the SystemACE Compact Flash as a set of image files
 * @param idx index of image to write (0-7)
 *
 * @return 0 for success, -1 for failure
 */
int writeImage(unsigned int idx)
{
	// sysace_fwrite, _fclose, _chdir etc
	return 42;
}

/**
 * Writes an empty test file to the CF
 */
void testCF(void)
{

	char data[] = {'H','e','l','l','o',' ','w','o','r','l','d','!',13,10 };
	void *pHandle;
	int retVal;

	pHandle = sysace_fopen("a:\\test.txt", "w");

	if (pHandle == NULL)
	{
		DBGOUT("sysace: Failed to open file for output.\r\n");
		return;
	}

	retVal = sysace_fwrite(data, 1, sizeof(data), pHandle);

	if (retVal==-1)
	{
		DBGOUT("sysace: Test file write failed.\r\n");
	}
	else
	{
		DBGOUT("sysace: Test file write OK!\r\n");
	}

	sysace_fclose(pHandle);

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

	// TODO: Remove this function

	// THIS CODE IS ADDED TO ORIGINAL XSYSACE_SELFTEST AS DIAGS!
/*
	int status;
	status = (XSysAce_GetStatusReg(InstancePtr->BaseAddress));// & XSA_SR_CFGLOCK_MASK);
	DBGOUT("hurfDurf: SystemACE status is 0x%x\r\n",status);
	status = XSysAce_Lock(InstancePtr, TRUE);
	DBGOUT("hurfDurf: Trying to lock SystemACE... ");
	if (status!=XST_SUCCESS) { DBGOUT("failed.\r\n"); } else { DBGOUT("OK!\r\n"); }
	if (XSysAce_IsMpuLocked(InstancePtr->BaseAddress)) {
		DBGOUT("hurfDurf: SystemACE lock is ENABLED\r\n");
	} else {
		DBGOUT("hurfDurf: SystemACE lock is DISABLED\r\n");
	}
*/

	Xil_AssertNonvoid(InstancePtr != NULL);
	Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

	/*
	 * Grab a lock (expect immediate success)
	 */
	Result = XSysAce_Lock(InstancePtr, TRUE);
	if (Result != XST_SUCCESS) {
		DBGOUT("hurfDurf: failed at lock (%d)\r\n", Result);
		return Result;
	}

	/*
	 * Verify the lock was retrieved
	 */
	if (!XSysAce_IsMpuLocked(InstancePtr->BaseAddress)) {
		DBGOUT("hurfDurf: failed at lock verify\r\n");
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
		DBGOUT("hurfDurf: failed at lock release\r\n");
		return XST_FAILURE;
	}

	/*
	 * If there are currently any errors on the device, fail self-test
	 */
	if (XSysAce_GetErrorReg(InstancePtr->BaseAddress) != 0) {
		DBGOUT("hurfDurf: ErrorReg: 0x%x\r\n", XSysAce_GetErrorReg(InstancePtr->BaseAddress));
		return XST_FAILURE;
	}

	return XST_SUCCESS;
}
