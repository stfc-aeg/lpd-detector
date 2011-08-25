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

// This define controls whether we are running on an ML507 dev. board, or a real FEM.
// For use on FEM, comment this line out!
#define HW_PLATFORM_DEVBOARD

// Hardware base addresses, redefine xparameters.h

// ML507 specific base address mappings
#ifdef HW_PLATFORM_ML507
#define BADDR_GP_LED8				XPAR_LEDS_8BIT_BASEADDR
#define BADDR_GP_LED5				XPAR_LEDS_POSITIONS_BASEADDR
#define BADDR_GP_DIP				XPAR_DIP_SWITCHES_8BIT_BASEADDR
#define BADDR_GP_SWITCH				XPAR_PUSH_BUTTONS_5BIT_BASEADDR
#endif

// FEM Hardware base address mappings
#define BADDR_I2C_LM82				XPAR_IIC_0_BASEADDR			// LM82
#define BADDR_I2C_EEPROM			XPAR_IIC_0_BASEADDR			// EEPROM
#define BADDR_I2C_SP3_TOP			XPAR_IIC_0_BASEADDR			// Spartan 3AN - Top
#define BADDR_I2C_SP3_BOT			XPAR_IIC_0_BASEADDR			// Spartan 3AN - Bottom
#define BADDR_MAC					XPAR_LLTEMAC_0_BASEADDR
#define BADDR_INTC					XPAR_XPS_INTC_0_BASEADDR
#define BADDR_RDMA					XPAR_RS232_UART_2_BASEADDR

// Enable / disable serial debugging output (comment to disable)
#define GLOBAL_DEBUG

#ifdef  GLOBAL_DEBUG
	#define DBGOUT(...)		xil_printf(__VA_ARGS__)
#else
	#define DBGOUT(...)
#endif

// Define an absolute maximum temperature threshold for the LM82.
// Overrides the value in EEPROM if (EEPROM_CRIT_TEMP > CRIT_TEMP_MAX)
#define CRIT_TEMP_MAX				90

// TODO: Tune these!
// ----------------------------------------------------------
#define THREAD_STACKSIZE 			4096
#define SOCK_BACKLOG				1

#endif /* FEM_H_ */
