/*
 * i2c.c
 *
 * I2C abstraction layer for Xilinx
 *
 */

#include "i2c.h"

/**
 * Initialises the I2C controllers ready for use
 *
 * @return operation status (XST_SUCCESS or error)
 */
int initI2C(void)
{
	int status;

	// Initialise I2C drivers
	status = XIic_Initialize(&iicLm82, XPAR_IIC_1_DEVICE_ID);
	if (status!=XST_SUCCESS) { return status; }
	/*
	status = XIic_Initialize(&iicEeprom, XPAR_IIC_0_DEVICE_ID);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Initialize(&iicRhs, XPAR_IIC_2_DEVICE_ID);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Initialize(&iicLhs, XPAR_IIC_3_DEVICE_ID);
	if (status!=XST_SUCCESS) { return status; }
	*/

	// Register ISRs (all share same ISRs as only one can be active at a time...)
	// LM82
	XIic_SetStatusHandler(&iicLm82, &iicLm82, (XIic_StatusHandler)statusHandler);
	XIic_SetSendHandler(&iicLm82, &iicLm82, (XIic_StatusHandler)sendHandler);
	XIic_SetRecvHandler(&iicLm82, &iicLm82, (XIic_StatusHandler)recvHandler);

	/*
	// EEPROM
	XIic_SetStatusHandler(&iicEeprom, &iicEeprom, (XIic_StatusHandler)statusHandler);
	XIic_SetSendHandler(&iicEeprom, &iicEeprom, (XIic_StatusHandler)sendHandler);
	XIic_SetRecvHandler(&iicEeprom, &iicEeprom, (XIic_StatusHandler)recvHandler);

	// LHS Spartan
	XIic_SetStatusHandler(&iicLhs, &iicLhs, (XIic_StatusHandler)statusHandler);
	XIic_SetSendHandler(&iicLhs, &iicLhs, (XIic_StatusHandler)sendHandler);
	XIic_SetRecvHandler(&iicLhs, &iicLhs, (XIic_StatusHandler)recvHandler);

	// RHS Spartan
	XIic_SetStatusHandler(&iicRhs, &iicRhs, (XIic_StatusHandler)statusHandler);
	XIic_SetSendHandler(&iicRhs, &iicRhs, (XIic_StatusHandler)sendHandler);
	XIic_SetRecvHandler(&iicRhs, &iicRhs, (XIic_StatusHandler)recvHandler);
	*/

	// Start controllers
	status = XIic_Start(&iicLm82);
	if (status!=XST_SUCCESS) { return status; }
	/*
	status = XIic_Start(&iicEeprom);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Start(&iicRhs);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Start(&iicLhs);
	if (status!=XST_SUCCESS) { return status; }
	*/

	return status;
}



/**
 * Starts all I2C engines and enables interrupts
 *
 * @ return operation status (XST_SUCCESS or error)
 */
int startI2C(void)
{
	int status;

	status = XIic_Start(&iicLm82);
	if (status!=XST_SUCCESS) { return status; }
	/*
	status = XIic_Start(&iicEeprom);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Start(&iicRhs);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Start(&iicLhs);
	*/

	// Enable interrupts
	XIic_IntrGlobalEnable(XPAR_IIC_LM82_BASEADDR);
	/*
	XIic_IntrGlobalEnable(XPAR_IIC_EEPROM_BASEADDR);
	XIic_IntrGlobalEnable(XPAR_IIC_POWER_LHS_BASEADDR);
	XIic_IntrGlobalEnable(XPAR_IIC_POWER_RHS_BASEADDR);
	*/

	return status;
}



/**
 * Stops all I2C engines and disables interrupts
 *
 * @ return operation status (XST_SUCCESS or error)
 */
int stopI2C(void)
{
	int status;

	// Disable interrupts
	XIic_IntrGlobalDisable(XPAR_IIC_LM82_BASEADDR);
	/*
	XIic_IntrGlobalDisable(XPAR_IIC_EEPROM_BASEADDR);
	XIic_IntrGlobalDisable(XPAR_IIC_POWER_LHS_BASEADDR);
	XIic_IntrGlobalDisable(XPAR_IIC_POWER_RHS_BASEADDR);
	*/

	// Stop engines
	status = XIic_Stop(&iicLm82);
	if (status!=XST_SUCCESS) { return status; }
	/*
	status = XIic_Stop(&iicEeprom);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Stop(&iicRhs);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Stop(&iicLhs);
	*/

	return status;
}



/**
 *Resets all I2C engines
 * NOTE: THIS CALL CAN BLOCK!
 */
void resetI2C(void)
{
	XIic_Reset(&iicLm82);
	XIic_Reset(&iicEeprom);
	XIic_Reset(&iicRhs);
	XIic_Reset(&iicLhs);
}



/**
 * I2C status interrupt handler
 * @param pIic pointer to XIic instance
 * @param event event ID
 */
void statusHandler(XIic* pIic, int event)
{
	// Signal that bus is no longer busy
	busNotBusy = 0;
	xil_printf("[x]\r\n");
}



/**
 * I2C send interrupt handler
 * @param pIic pointer to XIic instance
 * @param byteCount size of completed I2C send operation in bytes
 */
void sendHandler(XIic* pIic, int byteCount)
{
	// Signal send is complete
	sendComplete = 0;
	xil_printf("[S]\r\n");
}



/**
 * I2C receive interrupt handler
 * @param pIic pointer to XIic instance
 * @param byteCount size of completed I2C receive operation in bytes
 */
void recvHandler(XIic* pIic, int byteCount)
{
	// Signal receive is complete
	recvComplete = 0;
	xil_printf("[R]\r\n");
}



/**
 * Performs I2C operation.  Will wait until I2C operation completes (signalled by interrupt)
 * or times out.
 * Should not be called by user code directly, but via writeI2C / readI2C functions
 *
 * @param interfaceIdx I2C bus index
 * @param opMode operation mode (IIC_OPERATION_READ or IIC_OPERATION_WRITE)
 * @param slaveAddr I2C slave address
 * @param pData pointer to data payload
 * @param dataLen length of payload in bytes
 *
 * @return operation status (XST_SUCCESS or error)
 **/
int doI2COperation(int interfaceIdx, int opMode, u8 slaveAddr, u8* pData, unsigned dataLen)
{

	int status;
	volatile int *pVal;
	XIic *pI;

	xil_printf("I2C: idx=%d, op=%d, addr=0x%08x, bytes=%d\r\n", interfaceIdx, opMode, slaveAddr, dataLen);

	// Make sure all flags are cleared
	sendComplete = 0;
	recvComplete = 0;
	busNotBusy = 0;

	// Determine XIic instance to use
	switch(interfaceIdx)
	{
	case 0:
		pI = &iicLm82;
		break;
	case 1:
		pI = &iicEeprom;
		break;
	case 2:
		pI = &iicRhs;
		break;
	case 3:
		pI = &iicLhs;
		break;
	default:
		// Invalid index
		return XST_FAILURE;
	}

	// Set slave address
	status = XIic_SetAddress(pI, XII_ADDR_TO_SEND_TYPE, slaveAddr);
	if (status!=XST_SUCCESS) { return status; }

	xil_printf("I2C: Address set OK\r\n");

	// Do operation
	switch(opMode)
	{
	// NOTE: XIic_MasterXXXX functions require dataLen + 1 (address byte!)

	case IIC_OPERATION_READ:
		status = XIic_MasterRecv(pI, pData, dataLen+1);
		xil_printf("I2C: XIic_MasterRecv complete\r\n");
		pVal = &recvComplete;
		break;
	case IIC_OPERATION_WRITE:
		xil_printf("I2C: Writing 0x%02x, 0x%02x\r\n", (u8*)pData[0], (u8*)pData[1]);
		status = XIic_MasterSend(pI, pData, dataLen+1);
		xil_printf("I2C: XIic_MasterSend complete\r\n");
		pVal = &sendComplete;
		break;
	default:
		return XST_FAILURE;
	}

	// Check operation status
	if (status==XST_IIC_GENERAL_CALL_ADDRESS)
	{
		// This error should never happen but if it does just return and exit
		return status;
	}
	else if (status==XST_IIC_BUS_BUSY)
	{
		// This will generate a callback to the function registered with XIic_SetStatusHandler
		xil_printf("I2C: LAST OPERATION BUS BUSY!\r\n");
		pVal = &busNotBusy;
	}

	// Flag operation in progress
	*pVal = 1;

	// Store which IIC instance this is for
	pIic = pI;

	xil_printf("I2C: Entering interrupt loop\r\n");

	// Spin in a timed loop and wait the interrupt we're interested in to fire, or timeout and give up
	/*
	XTime timeout, now;
	XTime_GetTime(&timeout);
	XTime_GetTime(&now);
	xil_printf("I2C: tNow=%ul, tTimeout=%ul\r\n", now, timeout);
	timeout+=100000;			// In CPU ticks
	xil_printf("I2C: tNow=%ul, tTimeout=%ul\r\n", now, timeout);
	while(*pVal!=0 && now<timeout)
	{
		XTime_GetTime(&now);
		xil_printf("I2C: tNow=%d\r\n", now);
	}
	*/

	// Rubbish loop-based timeout
	int count = 0;
	int max   = 100000;
	while (*pVal!=0 && count<max)
	{
		count++;
	}

	xil_printf("I2C: Out of interrupt loop (%d)\r\n", count);

	// Did we timeout?
	if (*pVal!=0)
	{
		status = stopI2C();
		if (status==XST_IIC_BUS_BUSY)
		{
			// Always seems to trigger!
			xil_printf("I2C: Bus was busy while stopping\r\n");
			//startI2C();
		}
		else
		{
			xil_printf("I2C: Stop OK\r\n");
			startI2C();
		}

		xil_printf("I2C: Timed out\r\n");

		return XST_FAILURE;
	}

	xil_printf("I2C: Operation OK!\r\n");

	return XST_SUCCESS;
}


/**
 * Performs a write transaction to an I2C slave device.
 * @param slaveAddr I2C slave address
 * @param pData pointer to data buffer to write from
 * @param dataLen length of data (in bytes) to write
 *
 * @return number of bytes written
 */
int writeI2C(int interfaceIdx, u8 slaveAddr, u8* pData, unsigned dataLen)
{
	return doI2COperation(0, IIC_OPERATION_WRITE, slaveAddr, pData, dataLen);
}


/**
 * Performs a read transaction from an I2C slave device.
 * @param slaveAddr I2C slave address
 * @param pData pointer to data buffer to read to
 * @param dataLen length of data (in bytes) to read
 * @param bAddr hardware base address of I2C controller to use
 *
 * @return number of bytes read
 */
int readI2C(int interfaceIdx, u8 slaveAddr, u8* pData, unsigned dataLen)
{
	return doI2COperation(0, IIC_OPERATION_READ, slaveAddr, pData, dataLen);
}
