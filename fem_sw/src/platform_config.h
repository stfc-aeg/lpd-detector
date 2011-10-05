#ifndef __PLATFORM_CONFIG_H_
#define __PLATFORM_CONFIG_H_

//#define STDOUT_IS_16550
#ifdef STDOUT_IS_16550
#define STDOUT_BASEADDR XPAR_RS232_UART_PPC2_BASEADDR
#endif
#ifdef __PPC__
#define CACHEABLE_REGION_MASK 0xc0000001
#endif

#endif
