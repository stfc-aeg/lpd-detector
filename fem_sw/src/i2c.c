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
	XIic_SetSendHandler(&iicLm82, &iicLm82, (XIic_Handler)sendHandler);
	XIic_SetRecvHandler(&iicLm82, &iicLm82, (XIic_Handler)recvHandler);

	/*
	// EEPROM
	XIic_SetStatusHandler(&iicEeprom, &iicEeprom, (XIic_StatusHandler)statusHandler);
	XIic_SetSendHandler(&iicEeprom, &iicEeprom, (XIic_Handler)sendHandler);
	XIic_SetRecvHandler(&iicEeprom, &iicEeprom, (XIic_Handler)recvHandler);

	// LHS Spartan
	XIic_SetStatusHandler(&iicLhs, &iicLhs, (XIic_StatusHandler)statusHandler);
	XIic_SetSendHandler(&iicLhs, &iicLhs, (XIic_Handler)sendHandler);
	XIic_SetRecvHandler(&iicLhs, &iicLhs, (XIic_Handler)recvHandler);

	// RHS Spartan
	XIic_SetStatusHandler(&iicRhs, &iicRhs, (XIic_StatusHandler)statusHandler);
	XIic_SetSendHandler(&iicRhs, &iicRhs, (XIic_Handler)sendHandler);
	XIic_SetRecvHandler(&iicRhs, &iicRhs, (XIic_Handler)recvHandler);
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
 * Resets all I2C engines
 *
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
 * I2C status ISR
 * @param pIic pointer to XIic instance
 * @param event event ID
 */
static void statusHandler(XIic* pIic, int event)
{

	switch(event)
	{
	case XII_BUS_NOT_BUSY_EVENT:
		// Bus transitioned to not busy
		// NOTE: Due to a bug in 2.01a (xiic_intr.c) the XIic_BusNotBusyFuncPtr will assert
		//       so it is important to ensure the bus is not busy before reading / writing!
		busNotBusy = 0;
		break;

	case XII_SLAVE_NO_ACK_EVENT:
		// Slave did not ACK (had error)
		slaveNoAck = 1;
		break;

		// Events below should never occur on the FEM!
		// --------------------------------------------------------------------
	case XII_ARB_LOST_EVENT:
		// Arbitration was lost
	case XII_MASTER_READ_EVENT:
		// Master reading from slave
	case XII_MASTER_WRITE_EVENT:
		// Master writing to slave
	case XII_GENERAL_CALL_EVENT:
		// General call to all slaves
	default:
		iicError = 1;
		break;
		// --------------------------------------------------------------------

	}
}



/**
 * I2C send ISR
 * @param pIic pointer to XIic instance
 * @param byteCount size of completed I2C send operation in bytes
 */
static void sendHandler(XIic* pIic, int byteCount)
{
	numBytes = byteCount;
	sendComplete = 0;
}



/**
 * I2C receive ISR
 * @param pIic pointer to XIic instance
 * @param byteCount size of completed I2C receive operation in bytes
 */
static void recvHandler(XIic* pIic, int byteCount)
{
	numBytes = byteCount;
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
 * @return number of data bytes sent / received or -1 on an error
 **/
int doI2COperation(int interfaceIdx, int opMode, u8 slaveAddr, u8* pData, unsigned dataLen)
{

	int status;
	volatile int *pVal;
	XIic *pI;

	u32 iicSR = 0;
	u8 busBusy = 1;

	int count = 0;
	int max = 10000;

	// Clear status flags
	numBytes = 0;
	slaveNoAck = 0;
	iicError = 0;
	sendComplete = 0;
	recvComplete = 0;
	busNotBusy = 0;

	// Determine XIic instance to use
	switch(interfaceIdx)
	{
	case IIC_IDX_LM82:
		pI = &iicLm82;
		break;

	case IIC_IDX_EEPROM:
		pI = &iicEeprom;
		break;

	case IIC_IDX_PWR_RHS:
		pI = &iicRhs;
		break;

	case IIC_IDX_PWR_LHS:
		pI = &iicLhs;
		break;

	default:
		// Invalid index
		return -1;
	}

	// Store which IIC instance this is for
	pIic = pI;

	// Wait for not busy (as XIic_BusNotBusyFuncPtr is invalid in Xilinx driver and will cause assert!)
	// TODO: Timeout
	count = 0;
	while(busBusy==1 && count<max)
	{
		iicSR = XIic_ReadReg(pI->BaseAddress, XIIC_SR_REG_OFFSET);
		if (iicSR & XIIC_SR_BUS_BUSY_MASK) {
			busBusy = 0;
		}
	}

	if (busBusy==1)
	{
		// Bus not ready for operation so return
		return -1;
	}

	// Set slave address
	status = XIic_SetAddress(pI, XII_ADDR_TO_SEND_TYPE, slaveAddr);
	if (status!=XST_SUCCESS) { return -1; }

	// Do I2C comms.
	switch(opMode)
	{

	// NOTE: XIic_MasterXXXX functions require dataLen + 1 (address byte!)
	case IIC_OPERATION_READ:
		pVal = &recvComplete;
		*pVal = 1;		// Flag operation in progress
		status = XIic_MasterRecv(pI, pData, dataLen+1);
		break;

	case IIC_OPERATION_WRITE:
		pVal = &sendComplete;
		*pVal = 1;		// Flag operation in progress
		status = XIic_MasterSend(pI, pData, dataLen+1);
		break;

	default:
		return -1;
	}

	// Check operation status
	if (status==XST_IIC_GENERAL_CALL_ADDRESS)
	{
		// This error should never happen but if it does just return and exit
		return -1;
	}
	else if (status==XST_IIC_BUS_BUSY)
	{
		// This will generate a callback to the function registered with XIic_SetStatusHandler

		// NOTE: As we check for busy before doing operation this should never happen
		//       (because it will crash the FEM!)
		pVal = &busNotBusy;
		*pVal = 1;
	}

	//xil_printf("I2C: Entering interrupt loop\r\n");

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
	// TODO: Replace with above
	count = 0;
	while ((*pVal!=0 && count<max) || slaveNoAck==1)
	{
		count++;
	}

	xil_printf("I2C: Out of interrupt loop (%d)\r\n", count);

	if (slaveNoAck==1)
	{
		return -1;
	}

	// Did we timeout?
	if (*pVal!=0)
	{
		status = stopI2C();
		if (status==XST_IIC_BUS_BUSY)
		{
			xil_printf("I2C: Bus was busy while stopping\r\n");
			//startI2C();
		}
		else
		{
			xil_printf("I2C: Stop OK\r\n");
			startI2C();
		}

		xil_printf("I2C: Timed out\r\n");
		return -1;
	}

	return numBytes-1;		// Take 1 byte off for address!
}


/**
 * Performs a write transaction to an I2C slave device.
 * @param interfaceIdx I2C device index
 * @param pData pointer to data buffer to write from
 * @param dataLen length of data (in bytes) to write
 *
 * @return number of bytes written
 */
int writeI2C(int interfaceIdx, u8 slaveAddr, u8* pData, unsigned dataLen)
{
	return doI2COperation(interfaceIdx, IIC_OPERATION_WRITE, slaveAddr, pData, dataLen);
}


/**
 * Performs a read transaction from an I2C slave device.
 * @param interfaceIdx I2C device index
 * @param pData pointer to data buffer to read to
 * @param dataLen length of data (in bytes) to read
 * @param bAddr hardware base address of I2C controller to use
 *
 * @return number of bytes read
 */
int readI2C(int interfaceIdx, u8 slaveAddr, u8* pData, unsigned dataLen)
{
	return doI2COperation(interfaceIdx, IIC_OPERATION_READ, slaveAddr, pData, dataLen);
}
