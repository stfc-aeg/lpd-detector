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

// Hardware base addresses, device IDs and general settings from xparameters.h

// ML507 dev board
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
// FEM hardware
// Base addresses
#define BADDR_MAC					XPAR_LLTEMAC_0_BASEADDR
#define BADDR_INTC					XPAR_XPS_INTC_2_BASEADDR
#define BADDR_RDMA					XPAR_RS232_UART_PPC2_RDMA_BASEADDR
#define BADDR_MBOX					XPAR_MAILBOX_0_IF_1_BASEADDR
#define BADDR_BRAM					XPAR_SHARED_BRAM_IF_CNTLR_PPC_2_BASEADDR

// Device IDs
#define XINTC_ID					XPAR_XPS_INTC_2_DEVICE_ID
#define XSYSACE_ID					XPAR_SYSACE_0_DEVICE_ID
#define TIMER_ID					XPAR_XPS_TIMER_0_DEVICE_ID
#define MBOX_ID						XPAR_MAILBOX_0_IF_1_DEVICE_ID
#define RDMA_DEVICEID				XPAR_RS232_UART_PPC2_RDMA_DEVICE_ID
#define GPIO_ID						XPAR_XPS_GPIO_0_DEVICE_ID
#define IIC_LM82_ID					XPAR_IIC_1_DEVICE_ID
#define IIC_EEPROM_ID				XPAR_IIC_0_DEVICE_ID
#define IIC_PWR_RHS_ID				XPAR_IIC_3_DEVICE_ID
#define IIC_PWR_LHS_ID				XPAR_IIC_2_DEVICE_ID

// Mailbox settings
#define MBOX_RECV_ID				XPAR_MAILBOX_0_IF_1_RECV_FSL
#define MBOX_SEND_ID				XPAR_MAILBOX_0_IF_1_SEND_FSL
#define MBOX_USE_FSL				XPAR_MAILBOX_0_IF_1_USE_FSL

// RDMA settings
#define RDMA_CLK					XPAR_RS232_UART_PPC2_CLOCK_FREQ_HZ

// I2C interrupt vector IDs
#define I2C_INT_ID_EEPROM			XPAR_INTC_0_IIC_0_VEC_ID
#define I2C_INT_ID_LM82				XPAR_INTC_0_IIC_1_VEC_ID
#define I2C_INT_ID_PWR_LHS			XPAR_INTC_0_IIC_2_VEC_ID
#define I2C_INT_ID_PWR_RHS			XPAR_INTC_0_IIC_3_VEC_ID
#endif

// DDR2 memory size
#define FEM_DDR2_START				0x40000000
#define FEM_DDR2_SIZE				0x3FFFFFFF

// Uncomment this line if data caching enabled on PPC
//#define USE_CACHE		1

// UART baud rate
#define FEM_UART_BAUD				115200

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
#define NET_MAX_CLIENTS				8
#define NET_THREAD_STACKSIZE 		1024
#define NET_SOCK_BACKLOG			1					// Accept queue size for LWIP
#define NET_NOMINAL_RX_BUFFER_SZ	8192				// Normal payload receive buffer size
#define NET_LRG_RX_BUFFER_SZ		65536				// Large payload receive chunk size
#define NET_MAX_PAYLOAD_SZ			1048576				// Maximum payload size permitted
#define NET_DEFAULT_TICK_SEC		2
#define NET_DEFAULT_TICK_USEC		0
#define NET_DEFAULT_TIMEOUT_LIMIT	5					// In ticks

// Hardware initialisation bits - if set these signal errors occurred
// TODO: Refactor as enum
// ****************************************************************************
// Timer
#define TEST_TIMER_INIT				0x00000001		//! XPS Timer init.
#define TEST_TIMER_CALIB			0x00000002		//! Timer calibration

// Interrupt controller
#define TEST_INTC_INIT				0x00000004		//! Interrupt controller init.
#define TEST_INTC_START				0x00000008		//! Interrupt controller start
#define TEST_INTC_BIST				0x00000010		//! Interrupt controller self-test
#define TEST_INTC_CON_LM82			0x00000020		//! Interrupt controller LM82 interrupt connect
#define TEST_INTC_CON_EEPROM		0x00000040		//! Interrupt controller EEPROM interrupt connect
#define TEST_INTC_CON_PWR_RHS		0x00000080		//! Interrupt controller PWR_RHS interrupt connect
#define TEST_INTC_CON_PWR_LHS		0x00000100		//! Interrupt controller PWR_LHS interrupt connect

// RDMA / RDMA MUX / UART
#define TEST_RDMA_UART_BIST			0x00000200		//! RDMA UART self-test (loopback test)
#define TEST_GPIO_MUX_INIT			0x00000400		//! RDMA MUX init.

// SystemACE
#define TEST_SYSACE_INIT			0x00000800		//! SystemACE init.
#define TEST_SYSACE_BIST			0x00001000		//! SystemACE self-test
#define TEST_SYSACE_FILESYSTEM		0x00002000		//! SystemACE filesystem test

// Mailbox
#define TEST_MBOX_INIT				0x00004000		//! Mailbox init.

// I2C
#define TEST_I2C_INIT				0x00008000		//! I2C init.
#define TEST_I2C_LM82_INIT			0x00010000		//! LM82 init.
#define TEST_I2C_LM82_EXT_T_READ	0x00020000		//! LM82 external (V5) temp. read
#define TEST_I2C_LM82_INT_T_READ	0x00040000		//! LM82 internal (LM82 device) temp. read
#define TEST_I2C_EEPROM_CFG_READ	0x00080000		//! Config EEPROM read

// Frontend Personality Module (FPM)
#define TEST_FPM_INIT				0x00100000		//! FPM hardware init.
// ****************************************************************************

#define ERR_STRING_MAX_LENGTH		80				//! Buffer for error messages (per client)

//! Error code offsets
#define ERR_CODE_NETWORK_OFFSET		100
#define ERR_CODE_RDMA_OFFSET		200
#define ERR_CODE_I2C_OFFSET			300
#define ERR_CODE_EEPROM_OFFSET		400
#define ERR_CODE_INTERNAL_OFFSET	500
#define ERR_CODE_FPM_OFFSET			900

//! Global error codes
enum errorCodes {
	// Protocol errors
	ERR_PAYLOAD_TOO_BIG= 			ERR_CODE_NETWORK_OFFSET,		// TODO: Too vague, remove
	ERR_CLIENT_RESPONSE_TOO_BIG,
	ERR_HDR_INVALID_MAGIC,
	ERR_HDR_INVALID_PAYLOAD_SZ,
	ERR_HDR_INVALID_DATA_WIDTH,
	ERR_HDR_INVALID_ADDRESS,
	ERR_HDR_INVALID_RW_STATE,
	ERR_HDR_INVALID_BUS,
	ERR_HDR_INVALID_COMMAND,

	// RDMA errors
	ERR_RDMA_READ = 				ERR_CODE_RDMA_OFFSET,
	ERR_RDMA_WRITE,

	// I2C errors
	ERR_I2C_INVALID_BUS_INDEX =		ERR_CODE_I2C_OFFSET,
	ERR_I2C_SLAVE_NACK,
	ERR_I2C_TIMEOUT,
	ERR_I2C_BUSY,
	ERR_I2C_ADDRESS_ERROR,
	ERR_I2C_INVALID_OPMODE,
	ERR_I2C_GENERAL_CALL,
	ERR_I2C_UNKNOWN_ERROR,

	// EEPROM errors
	ERR_EEPROM_BAD_CHECKSUM =		ERR_CODE_EEPROM_OFFSET,

	// Internal errors
	ERR_ACQ_CONFIG_NACK =			ERR_CODE_INTERNAL_OFFSET,
	ERR_ACQ_CONFIG_BAD_ACK,
	ERR_ACQ_OP_NACK,
	ERR_ACQ_OP_BACK_ACK,
	ERR_RX_MALLOC_FAILED
};

#endif /* FEM_H_ */

