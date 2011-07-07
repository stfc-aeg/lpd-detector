/*
 * rdma.c
 *
 * Abstraction layer for Xilinx register operations
 * Provides RDMA-like access to memory mapped peripheral address space
 *
 */

#include "rdma.h"

// Returns 32bit register value at addr
u32 readRegister_32(u32 addr)
{
	return Xil_In32(addr);
}

// Writes 32bit value to addr
void writeRegister_32(u32 addr, u32 value)
{
	Xil_Out32(addr, value);
}

// Returns 16bit register value at addr
u16 readRegister_16(u32 addr)
{
	return Xil_In16(addr);
}

// Writes 16bit value to addr
void writeRegister_16(u32 addr, u16 value)
{
	Xil_Out16(addr, value);
}

// Returns 8bit register value at addr
u8 readRegister_8(u32 addr)
{
	return Xil_In8(addr);
}

// Writes 8bit value to addr
void writeRegister_8(u32 addr, u8 value)
{
	Xil_Out8(addr, value);
}
