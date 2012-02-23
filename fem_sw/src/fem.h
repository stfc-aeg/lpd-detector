/*
 * fem.h
 *
 * Main header file for FEM card
 * Includes all base address definitions from xparameters.h
 *
 */

#ifndef FEM_H_
#define FEM_H_

#include "xparameters.h"
#include "xil_types.h"

// ****************************************************************************
// This define controls whether we are running on an ML507 dev. board, or a real FEM.
// For use on FEM, comment this line out!
// ****************************************************************************
//#define HW_PLATFORM_DEVBOARD
// ****************************************************************************

// Hardware base addresses, redefine xparameters.h

// ML507 specific base address mappings
#ifdef HW_PLATFORM_DEVBOARD
// Devices only present on ML507
#define BADDR_GP_LED8				XPAR_LEDS_8BIT_BASEADDR
#define BADDR_GP_LED5				XPAR_LEDS_POSITIONS_BASEADDR
#define BADDR_GP_DIP				XPAR_DIP_SWITCHES_8BIT_BASEADDR
#define BADDR_GP_SWITCH				XPAR_PUSH_BUTTONS_5BIT_BASEADDR
// Devices on both ML507 and FEM
#define BADDR_I2C_LM82				XPAR_IIC_0_BASEADDR			// LM82
#define BADDR_I2C_EEPROM			XPAR_IIC_0_BASEADDR			// EEPROM
#define BADDR_I2C_SP3_TOP			XPAR_IIC_0_BASEADDR			// Spartan 3AN - Top
#define BADDR_I2C_SP3_BOT			XPAR_IIC_0_BASEADDR			// Spartan 3AN - Bottom
#define BADDR_MAC					XPAR_LLTEMAC_0_BASEADDR
#define BADDR_INTC					XPAR_XPS_INTC_0_BASEADDR
#define BADDR_RDMA					XPAR_RS232_UART_2_BASEADDR
#define XINTC_ID					XPAR_XPS_INTC_0_DEVICE_ID
#define XSYSACE_ID					XPAR_SYSACE_0_DEVICE_ID

#else
// FEM devices
#define BADDR_I2C_LM82				XPAR_IIC_LM82_BASEADDR
#define BADDR_I2C_EEPROM			XPAR_IIC_EEPROM_BASEADDR
#define BADDR_I2C_SP3_TOP			XPAR_IIC_POWER_RHS_BASEADDR
#define BADDR_I2C_SP3_BOT			XPAR_IIC_POWER_LHS_BASEADDR
#define BADDR_MAC					XPAR_LLTEMAC_0_BASEADDR
#define BADDR_INTC					XPAR_XPS_INTC_2_BASEADDR
#define BADDR_RDMA					XPAR_RS232_UART_PPC2_RDMA_BASEADDR
#define BADDR_MBOX					XPAR_MAILBOX_0_IF_1_BASEADDR
#define XINTC_ID					XPAR_XPS_INTC_2_DEVICE_ID
#define XSYSACE_ID					XPAR_SYSACE_0_DEVICE_ID
#define MBOX_ID						XPAR_MAILBOX_0_IF_1_DEVICE_ID
#define MBOX_RECV_ID				XPAR_MAILBOX_0_IF_1_RECV_FSL
#define MBOX_SEND_ID				XPAR_MAILBOX_0_IF_1_SEND_FSL
#define MBOX_USE_FSL				XPAR_MAILBOX_0_IF_1_USE_FSL
#endif

// Enable / disable serial debugging output (comment to disable)
#define GLOBAL_DEBUG

#ifdef  GLOBAL_DEBUG
	#define DBGOUT(...)		xil_printf(__VA_ARGS__)
#else
	#define DBGOUT(...)
#endif

// Network protocol debugging
//#define PROTOCOL_DEBUG
#ifdef	PROTOCOL_DEBUG
	#define	PRTDBG(...)		xil_printf(__VA_ARGS__)
#else
	#define PRTDBG(...)
#endif

// Define an absolute maximum temperature threshold for the LM82.
// Overrides the value in EEPROM if (EEPROM_CRIT_TEMP > CRIT_TEMP_MAX)
#define CRIT_TEMP_MAX				90

// FEM Networking parameters
#define NET_CMD_PORT				6969
#define NET_MAX_CLIENTS				2
#define NET_THREAD_STACKSIZE 		1024
#define NET_SOCK_BACKLOG			1					// Accept queue size for LWIP
#define NET_NOMINAL_RX_BUFFER_SZ	2048				// Normal payload receive buffer size
#define NET_LRG_PKT_INCREMENT_SZ	65536				// Large payload receive chunk size
#define NET_MAX_PAYLOAD_SZ			1048576				// Maximum payload size permitted
#define NET_DEFAULT_TICK_SEC		2
#define NET_DEFAULT_TICK_USEC		0
#define NET_DEFAULT_TIMEOUT_LIMIT	5					// In ticks

// Self-test bits - if set these represent a failure during hardware init!
#define TEST_XPSTIMER_INIT			0x0001
#define TEST_TIMER_CALIB			0x0002
#define TEST_XINTC_INIT				0x0004
#define TEST_XINTC_START			0x0008
#define TEST_RDMA_UART_OK			0x0010
#define TEST_RDMA_READBACK			0x0020
#define TEST_SYSACE_INIT			0x0040
#define TEST_SYSACE_BIST			0x0080

#define TEST_EEPROM_CFG_READ		0x8000

#endif /* FEM_H_ */

