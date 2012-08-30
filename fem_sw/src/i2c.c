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
	status = XIic_Initialize(&iicLm82, 0);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Initialize(&iicEeprom, 0);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Initialize(&iicRhs, 0);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Initialize(&iicLhs, 0);
	if (status!=XST_SUCCESS) { return status; }

	// Start controllers
	status = XIic_Start(&iicLm82);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Start(&iicEeprom);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Start(&iicRhs);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Start(&iicLhs);
	if (status!=XST_SUCCESS) { return status; }

	// Register ISRs (all share same ISRs as only one can be active at a time...)
	// LM82
	XIic_SetStatusHandler(&iicLm82, &iicLm82, (XIic_StatusHandler)statusHandler);
	XIic_SetSendHandler(&iicLm82, &iicLm82, (XIic_StatusHandler)sendHandler);
	XIic_SetRecvHandler(&iicLm82, &iicLm82, (XIic_StatusHandler)recvHandler);

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
	status = XIic_Start(&iicEeprom);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Start(&iicRhs);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Start(&iicLhs);

	// Enable interrupts
	XIic_IntrGlobalEnable(XPAR_IIC_LM82_BASEADDR);
	XIic_IntrGlobalEnable(XPAR_IIC_EEPROM_BASEADDR);
	XIic_IntrGlobalEnable(XPAR_IIC_POWER_LHS_BASEADDR);
	XIic_IntrGlobalEnable(XPAR_IIC_POWER_RHS_BASEADDR);

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

	status = XIic_Stop(&iicLm82);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Stop(&iicEeprom);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Stop(&iicRhs);
	if (status!=XST_SUCCESS) { return status; }
	status = XIic_Stop(&iicLhs);

	// Disable interrupts
	XIic_IntrGlobalDisable(XPAR_IIC_LM82_BASEADDR);
	XIic_IntrGlobalDisable(XPAR_IIC_EEPROM_BASEADDR);
	XIic_IntrGlobalDisable(XPAR_IIC_POWER_LHS_BASEADDR);
	XIic_IntrGlobalDisable(XPAR_IIC_POWER_RHS_BASEADDR);

	return status;
}



/**
 *Resets all I2C engines
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
	XTime timeout, now;

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

	// Do operation
	switch(opMode)
	{
	case IIC_OPERATION_READ:
		status = XIic_MasterRecv(pI, pData, dataLen);
		pVal = &recvComplete;
		break;
	case IIC_OPERATION_WRITE:
		status = XIic_MasterSend(pI, pData, dataLen);
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
		pVal = &busNotBusy;
	}

	// Flag operation in progress
	*pVal = 1;

	// Store which IIC instance this is for
	pIic = pI;

	// Spin in a timed loop and wait the interrupt we're interested in to fire, or timeout and give up
	XTime_GetTime(&timeout);
	timeout+=100000;			// In CPU ticks

	XTime_GetTime(&now);
	while(*pVal!=0 && now<timeout)
	{
		XTime_GetTime(&now);
	}

	// Did we timeout?
	if (*pVal!=0)
	{
		status = stopI2C();
		if (status==XST_IIC_BUS_BUSY)
		{
			// TODO: Deal with bus busy, another timeout loop?
			// Will this ever happen if previous operation timed out??
		}
		startI2C();
		return XST_FAILURE;
	}

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
	return doI2COperation(0, IIC_OPERATION_READ, slaveAddr, pData, dataLen);
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
	return doI2COperation(0, IIC_OPERATION_WRITE, slaveAddr, pData, dataLen);
}
