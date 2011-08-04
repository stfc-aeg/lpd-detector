/*
 * rdma.h
 *
 * Provides access to ESDG group FPGA blocks via
 * RS232-RDMA link
 *
 */

#include "xil_types.h"
#include "xuartlite_l.h"
#include "xtmrctr.h"

#ifndef RDMA_H_
#define RDMA_H_

#define RDMA_CMD_READ			0
#define RDMA_CMD_WRITE			1

u32 readRdma(u32 base, u32 addr);
void writeRdma(u32 base, u32 addr, u32 value);

#endif /* RDMA_H_ */
