/*
 * raw.h
 *
 * Abstraction layer for Xilinx register operations
 * Provides RDMA-like access to memory mapped peripheral address space
 *
 */

#ifndef RAW_H_
#define RAW_H_

#include "xil_io.h"

// Wrapper methods for memory access
u32 readRegister_32(u32 addr);
void writeRegister_32(u32 addr, u32 value);

u16 readRegister_16(u32 addr);
void writeRegister_16(u32 addr, u16 value);

u8 readRegister_8(u32 addr);
void writeRegister_8(u32 addr, u8 value);


#endif /* RAW_H_ */
