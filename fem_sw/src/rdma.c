/*
 * rdma.c
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

#include "rdma.h"

/*
 * Reads 32bit RDMA register
 * @param base base address of UART to read from
 * @param addr register address to read
 *
 * @return register value
 *
 */
u32 readRdma(u32 base, u32 addr)
{
	int i;
	u8 thisByte = 0;
	u32 readVal = 0;

	UART_SEND(base, RDMA_CMD_READ);

	// Send address (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (addr>>(8*i));
		UART_SEND(base, thisByte);
	}

	// Read value (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = UART_RECV(base);
		readVal |= (thisByte<<(8*i));
	}

	return readVal;
}

/*
 * Writes 32bit RDMA register
 * @param base base address of UART to write to
 * @param addr register address to write to
 * @param value value to write
 *
 */
void writeRdma(u32 base, u32 addr, u32 value)
{
	int i;
	u8 thisByte = 0;

	UART_SEND(base, RDMA_CMD_WRITE);

	// Send address (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (addr>>(8*i));
		UART_SEND(base, thisByte);
	}

	// Send value (4 bytes)
	for (i=0; i<4; i++)
	{
		thisByte = 0xFF & (value>>(8*i));
		UART_SEND(base, thisByte);
	}

}
