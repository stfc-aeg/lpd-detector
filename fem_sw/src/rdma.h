/*
 * rdma.h
 *
 * Provides access to ESDG group FPGA blocks via
 * RS232-RDMA link
 *
 */

#include "xil_types.h"
#include "fem.h"

#ifdef HW_PLATFORM_DEVBOARD
#include "xuartlite_l.h"
#define UART_SEND(baddr,byte)	XUartLite_SendByte(baddr,byte)
#define UART_RECV(baddr)		XUartLite_RecvByte(baddr)
#else
#include "xuartns550_l.h"
#define UART_SEND(baddr,byte)	XUartNs550_SendByte(baddr,byte)
#define UART_RECV(baddr)		XUartNs550_RecvByte(baddr)
#endif
#include "xtmrctr.h"

#ifndef RDMA_H_
#define RDMA_H_

#define RDMA_CMD_READ			0
#define RDMA_CMD_WRITE			1

u32 readRdma(u32 base, u32 addr);
void writeRdma(u32 base, u32 addr, u32 value);

#endif /* RDMA_H_ */
