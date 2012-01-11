/*
 * rdma.c
 *
 * Controls access to RDMA blocks through a UART
 *
 */

// TODO: Reformat 4x1 byte sends as single 4 byte transmission
// TODO: Add sleeps into polling loops
// TODO: Complete support for uartlite, or respin devboard build to use UART16550

/*
 * RDMA protocol format:
 * Command (1 byte)
 * Address (4 bytes LSB first)
 * Value (4 bytes LSB first) <- Only for write operations
 *
 */

#include "rdma.h"

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
	// TODO: Implement readback test
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

#else

static XUartNs550 uart;
static XUartNs550_Config uartCfg;
static XUartNs550Format uartFmt;

/*
 * Initialises RDMA controller
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

	return XST_SUCCESS;
}

/*
 * Performs self test on UART and RDMA block
 * @return one of XST_SUCCESS, XST_UART_TEST_FAIL, XST_LOOPBACK_ERROR
 */
int rdmaSelftest(void)
{
	int status = 0;

	// UART loopback test
	status = XUartNs550_SelfTest(&uart);
	if (status==XST_UART_TEST_FAIL) {
		return status;
	}

	// RDMA writeback test
	int testVal  = 0xA5FACE5A;
	int readVal  = 0;
	writeRdma(RDMA_SELFTEST_REG, testVal);
	readVal = readRdma(RDMA_SELFTEST_REG);
	if (readVal != testVal) {
		return XST_LOOPBACK_ERROR;
	}

	return XST_SUCCESS;

}

/*
 * Reads 32bit RDMA register
 * @param pUart pointer to UART object
 * @param base base address of UART to write to
 * @param addr register address to read
 *
 * @return register value
 *
 */
u32 readRdma(u32 addr)
{
	int i;
	int numBytes = 0;
	int numLoops = 0;
	int maxLoops = 5000;
	u8 thisByte = 0;
	u32 readVal = 0;

	thisByte = RDMA_CMD_READ;
	numLoops = 0;
	while ((numBytes==0) & (numLoops<maxLoops))
	{
		numBytes = XUartNs550_Send(&uart, &thisByte, 1);
		numLoops++;
	}
	numBytes=0;


	// Send address (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (addr>>(8*i));
		numLoops = 0;
		while ((numBytes==0) & (numLoops<maxLoops))
		{
			numBytes = XUartNs550_Send(&uart, &thisByte, 1);
			numLoops++;
		}
		numBytes=0;
	}

	// Read value (4 bytes)
	for (i=0; i<4; i++)
	{
		numLoops = 0;
		while ((numBytes==0) & (numLoops<maxLoops))
		{
			numBytes = XUartNs550_Recv(&uart, &thisByte, 1);
			numLoops++;
		}
		numBytes = 0;
		readVal |= (thisByte<<(8*i));
	}

	return readVal;
}

/*
 * Writes 32bit RDMA register
 * @param pUart pointer to UART object
 * @param base base address of UART to write to
 * @param addr register address to write to
 * @param value value to write
 *
 */
void writeRdma(u32 addr, u32 value)
{
	int i;
	u8 thisByte = 0;

	int numBytes = 0;
	int numLoops = 0;
	int maxLoops = 5000;

	thisByte = RDMA_CMD_WRITE;
	while ((numBytes==0) & (numLoops<maxLoops))
	{
		numBytes = XUartNs550_Send(&uart, &thisByte, 1);
		numLoops++;
	}
	numBytes = 0;
	numLoops = 0;

	// Send address (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (addr>>(8*i));
		while ((numBytes==0) & (numLoops<maxLoops))
		{
			numBytes = XUartNs550_Send(&uart, &thisByte, 1);
			numLoops++;
		}
		numBytes = 0;
		numLoops = 0;
	}

	// Send value (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (value>>(8*i));
		while ((numBytes==0) & (numLoops<maxLoops))
		{
			numBytes = XUartNs550_Send(&uart, &thisByte, 1);
			numLoops++;
		}
		numBytes = 0;
		numLoops = 0;
	}

}

#endif
