/*
 * rs232_rdma.c
 *
 *  Created on: Jul 25, 2011
 *      Author: mt47
 */

/*
 * RDMA protocol format:
 * Command (1 byte)
 * Address (4 bytes LSB first)
 * Value (4 bytes LSB first) (WRITES ONLY!)
 *
 */

#include "rs232_rdma.h"

// Returns 32bit register value at addr
u32 readRdma(u32 base, u32 addr)
{
	int i;
	u8 thisByte = 0;
	u32 readVal = 0;

	XUartLite_SendByte(base, RDMA_CMD_READ);

	// Send address (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (addr>>(8*i));
		XUartLite_SendByte(base, thisByte);
	}

	// Read value (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = XUartLite_RecvByte(base);
		//xil_printf("RDMA_R:  Read 0x%x\r\n",thisByte);
		readVal |= (thisByte<<(8*i));
	}
	return readVal;
}

// Writes 32bit value to addr
void writeRdma(u32 base, u32 addr, u32 value)
{
	int i;
	u8 thisByte = 0;

	XUartLite_SendByte(base, RDMA_CMD_WRITE);

	// Send address (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (addr>>(8*i));
		XUartLite_SendByte(base, thisByte);
		//xil_printf("RDMA_W: Write 0x%x\r\n",thisByte);
	}

	// Send value (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (value>>(8*i));
		XUartLite_SendByte(base, thisByte);
		//xil_printf("RDMA_W: Write 0x%x\r\n",thisByte);
	}

}
