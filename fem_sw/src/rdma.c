/*
 * rdma.c
 *
 * Controls access to RDMA blocks through a UART
 *
 */

// TODO: Reformat 4x1 byte sends as single 4 byte transmission

/*
 * RDMA protocol format:
 * Command (1 byte)
 * Address (4 bytes LSB first)
 * Value (4 bytes LSB first) <- Only for write operations
 *
 */

#include "rdma.h"

#ifndef HW_PLATFORM_DEVBOARD
u32 mux;
XGpio gpioMux;
#endif

// Separate implementations for both UART types
#ifdef HW_PLATFORM_DEVBOARD

/*
 * Initialises RDMA controller
 * @return one of XST_SUCCESS, XST_DEVICE_NOT_FOUND, XST_UART_BAUD_ERROR, XST_INVALID_PARAM
 */
int initRdma(void)
{
	// We don't initialise anything with uartlite so just return OK
	return XST_SUCCESS;
}

/*
 * Performs self test on UART and RDMA block
 * @return one of XST_SUCCESS, XST_UART_TEST_FAIL, XST_LOOPBACK_ERROR
 */
int rdmaSelftest(void)
{
	return XST_SUCCESS;
}

u32 readRdma(u32 addr)
{
	// Use BADDR_RDMA !
	return 0;
}

void writeRdma(u32 addr, u32 value)
{
	// Use BADDR_RDMA !
	return;
}

void setMux(u8 mux)
{
	return;
}

#else

static XUartNs550 uart;
static XUartNs550_Config uartCfg;
static XUartNs550Format uartFmt;

/**
 * Initialises the RDMA controller
 *
 * @return one of XST_SUCCESS, XST_DEVICE_NOT_FOUND, XST_UART_BAUD_ERROR, XST_INVALID_PARAM
 */
int initRdma(void)
{
	int status = 0;

	// Initialise UART
	status = XUartNs550_Initialize(&uart, RDMA_DEVICEID);
	if (status != XST_SUCCESS)
	{
		return status;
	}

	// Configure UART
	uartCfg.BaseAddress =		BADDR_RDMA;
	uartCfg.DeviceId =			RDMA_DEVICEID;
	uartCfg.InputClockHz =		RDMA_CLK;
	uartCfg.DefaultBaudRate =	RDMA_DEF_BAUDRATE;
	status = XUartNs550_CfgInitialize(&uart, &uartCfg, BADDR_RDMA);
	if (status!=XST_SUCCESS)
	{
		return status;
	}

	// Configure data format
	uartFmt.BaudRate =			RDMA_BAUDRATE;
	uartFmt.DataBits =			RDMA_DATABITS;
	uartFmt.Parity =			RDMA_PARITY;
	uartFmt.StopBits =			RDMA_STOPBITS;
	status = XUartNs550_SetDataFormat(&uart, &uartFmt);
	if (status!=XST_SUCCESS)
	{
		return status;
	}

	// Initialise GPIO mux, set to 0
#ifndef HW_PLATFORM_DEVBOARD
	mux = 0;
	status = XGpio_Initialize(&gpioMux, GPIO_ID);
	if (status!=XST_SUCCESS)
	{
		return status;
	}
	XGpio_SetDataDirection(&gpioMux, 1, 0x00);	// All outputs
	XGpio_DiscreteWrite(&gpioMux, 1, mux);
#endif

	return XST_SUCCESS;
}


/**
 * Performs self test on UART and RDMA block
 *
 * @return XST_SUCCESS or XST_UART_TEST_FAIL
 */
int rdmaSelftest(void)
{
	int status = 0;

	// UART loopback test
	status = XUartNs550_SelfTest(&uart);
	if (status==XST_UART_TEST_FAIL) {
		return status;
	}

	return XST_SUCCESS;
}

/**
 * Reads a 32bit RDMA register
 * @param addr register address to read
 * @param pVal pointer to u32 to store RDMA read value in
 *
 * @return operation status, XST_SUCCESS or XST_FAILURE
 */
int readRdma(u32 addr, u32 *pVal)
{
	int i;
	int numBytes = 0;
	int numLoops = 0;
	u8 thisByte = 0;
	u32 readVal = 0;

	thisByte = RDMA_CMD_READ;
	numLoops = 0;

	setMux(&addr);

	while ((numBytes==0) & (numLoops<RDMA_MAX_RETRIES))
	{
		numBytes = XUartNs550_Send(&uart, &thisByte, 1);
		numLoops++;
	}
	RDMA_CHECK_TIMEOUT(numLoops);
	numBytes=0;

	// Send address (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (addr>>(8*i));
		numLoops = 0;
		while ((numBytes==0) & (numLoops<RDMA_MAX_RETRIES))
		{
			numBytes = XUartNs550_Send(&uart, &thisByte, 1);
			numLoops++;
		}
		numBytes=0;
	}
	RDMA_CHECK_TIMEOUT(numLoops);

	// Read value (4 bytes)
	for (i=0; i<4; i++)
	{
		numLoops = 0;
		while ((numBytes==0) & (numLoops<RDMA_MAX_RETRIES))
		{
			numBytes = XUartNs550_Recv(&uart, &thisByte, 1);
			numLoops++;
		}
		numBytes = 0;
		readVal |= (thisByte<<(8*i));
	}
	RDMA_CHECK_TIMEOUT(numLoops);

	// All OK
	*pVal = readVal;
	return XST_SUCCESS;
}


/**
 * Writes a 32bit RDMA register
 * @param addr register address to write to
 * @param value value to write
 *
 * @return operation status, XST_SUCCESS or XST_FAILURE
 */
int writeRdma(u32 addr, u32 value)
{
	int i;
	u8 thisByte = 0;

	int numBytes = 0;
	int numLoops = 0;

	thisByte = RDMA_CMD_WRITE;

	setMux(&addr);

	while ((numBytes==0) & (numLoops<RDMA_MAX_RETRIES))
	{
		numBytes = XUartNs550_Send(&uart, &thisByte, 1);
		numLoops++;
	}
	RDMA_CHECK_TIMEOUT(numLoops);
	numBytes = 0;
	numLoops = 0;

	// Send address (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (addr>>(8*i));
		while ((numBytes==0) & (numLoops<RDMA_MAX_RETRIES))
		{
			numBytes = XUartNs550_Send(&uart, &thisByte, 1);
			numLoops++;
		}
		numBytes = 0;
		numLoops = 0;
	}
	RDMA_CHECK_TIMEOUT(numLoops);

	// Send value (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (value>>(8*i));
		while ((numBytes==0) & (numLoops<RDMA_MAX_RETRIES))
		{
			numBytes = XUartNs550_Send(&uart, &thisByte, 1);
			numLoops++;
		}
		numBytes = 0;
		numLoops = 0;
	}
	RDMA_CHECK_TIMEOUT(numLoops);

	// All OK
	return XST_SUCCESS;
}


/**
 * Sets RDMA GPIO mux (if necessary)
 */
void setMux(u32 *pAddr)
{
	u32 thisMux = (((*pAddr) & 0x30000000) >> 28);

	// Do mux, if necessary
	if (thisMux != mux) {
		//DBGOUT("setMux(): Mux was %d, setting to %d\r\n", mux, thisMux);
		XGpio_DiscreteWrite(&gpioMux, 1, thisMux);
		mux = thisMux;
	}

	// Unmangle address
	//DBGOUT("setMux(): Input RDMA address: 0x%08x\r\n", *pAddr);
	*pAddr = (((*pAddr & 0x0FFFFFFF) & 0x0F000000) << 4) | ((*pAddr & 0x0FFFFFFF) & 0x00FFFFFF);
	//DBGOUT("setMux(): Output RDMA address: 0x%08x\r\n", *pAddr);
}

#endif
