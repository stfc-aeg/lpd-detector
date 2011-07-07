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

// Hardware base addresses, redefine xparameters.h

// ----------------------------------------
// TODO: THIS SECTION ONLY FOR ML507 - REMOVE!
#define BADDR_GP_LED8				XPAR_LEDS_8BIT_BASEADDR
#define BADDR_GP_LED5				XPAR_LEDS_POSITIONS_BASEADDR
#define BADDR_GP_DIP				XPAR_DIP_SWITCHES_8BIT_BASEADDR
#define BADDR_GP_SWITCH				XPAR_PUSH_BUTTONS_5BIT_BASEADDR
// ----------------- END -------------------

// FEM Hardware base address mappings (from xparameters.h)
#define BADDR_MAC					XPAR_LLTEMAC_0_BASEADDR
#define BADDR_I2C					XPAR_IIC_0_BASEADDR
#define BADDR_INTC					XPAR_XPS_INTC_0_BASEADDR

// Enable / disable serial debugging output (comment to disable)
//#define GLOBAL_DEBUG

#ifdef  GLOBAL_DEBUG
	#define DBGOUT(...)		xil_printf(__VA_ARGS__)
#else
	#define DBGOUT(...)
#endif

// Define an absolute maximum temperature threshold for the LM82.
// Overrides the value in EEPROM if it is higher
#define CRIT_TEMP_MAX				90

// Struct for storage of FEM parameters in EEPROM
struct fem_config
{
	// For MAC
	u8 mac_address[6];

	// For hardware monitoring
	u8 temp_high_setpoint;
	u8 temp_crit_setpoint;

	// Versioning information
	u8 sw_major_version;
	u8 sw_minor_version;
	u8 fw_major_version;
	u8 fw_minor_version;
	u8 hw_major_version;
	u8 hw_minor_version;
	u8 board_id;
	u8 board_type;
};

#endif /* FEM_H_ */
