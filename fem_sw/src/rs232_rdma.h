/*
 * rs232_rdma.h
 *
 * Provides access to ESDG group FPGA blocks via
 * RS232-RDMA link
 *
 */

#include "xil_types.h"
#include "xuartlite_l.h"

#ifndef RS232_RDMA_H_
#define RS232_RDMA_H_

#define RDMA_CMD_READ			0
#define RDMA_CMD_WRITE			1

u32 readRdma(u32 base, u32 addr);
void writeRdma(u32 base, u32 addr, u32 value);

#endif /* RS232_RDMA_H_ */
