/*
 * raw.c
 *
 * Abstraction layer for Xilinx register operations
 * Provides RDMA-like access to memory mapped peripheral address space
 *
 */

#include "raw.h"

/*
 * Reads raw 32bit register
 * @param addr register address
 *
 * @return register value
 *
 */
u32 readRegister_32(u32 addr)
{
	return Xil_In32(addr);
}

/*
 * Writes raw 32bit register
 * @param addr register address
 * @param value value to write
 *
 */
void writeRegister_32(u32 addr, u32 value)
{
	Xil_Out32(addr, value);
}

/*
 * Reads raw 16bit register
 * @param addr register address
 *
 * @return register value
 *
 */
u16 readRegister_16(u32 addr)
{
	return Xil_In16(addr);
}

/*
 * Writes raw 16bit register
 * @param addr register address
 * @param value value to write
 *
 */
void writeRegister_16(u32 addr, u16 value)
{
	Xil_Out16(addr, value);
}

/*
 * Reads raw 8bit register
 * @param addr register address
 *
 * @return register value
 *
 */
u8 readRegister_8(u32 addr)
{
	return Xil_In8(addr);
}

/*
 * Writes raw 32bit register
 * @param addr register address
 * @param value value to write
 *
 */
void writeRegister_8(u32 addr, u8 value)
{
	Xil_Out8(addr, value);
}
