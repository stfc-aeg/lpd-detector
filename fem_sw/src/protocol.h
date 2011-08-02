/*
 * protocol.h
 *
 *  Basic protocol for FEM control and configuration over ethernet
 *
 */

#ifndef PROTOCOL_H_
#define PROTOCOL_H_

#include "xil_types.h"

#define MAX_PAYLOAD_SIZE          1024

#define PROTOCOL_MAGIC_WORD       0xDEADBEEF

// Bit manipulation macros
#define	CBIT(val,bit)		val &= ~(1 << (bit-1))
#define SBIT(val,bit)		val |=  (1 << (bit-1))
#define CMPBIT(val, bit)	val &   (1 << (bit-1))

// Macro to decode and display header
#ifdef GLOBAL_DEBUG
#define DUMPHDR(hdr)		xil_printf("Magic: 0x%x\r\n",hdr->magic); \
							xil_printf("Cmd:   0x%x\r\n",hdr->command); \
							xil_printf("Bus:   0x%x\r\n",hdr->bus_target); \
							xil_printf("Width: 0x%x\r\n",hdr->data_width); \
							xil_printf("Stat:  0x%x\r\n",hdr->status); \
							xil_printf("Addr:  0x%x\r\n",hdr->address); \
							xil_printf("Payld: %d\r\n", hdr->payload_sz)
#else
#define DUMPHDR(hdr)
#endif

// New header format
// Size     Description
// ----------------------------------------------------------------------------
//  32      Magic word   (must be 0xDEADBEEF)
//   8      Command type (must be 1)
//   8      Bus target   (see protocol_bus_type enum)
//   8      Data width   (see protocol_data_width enum)
//   8      Status byte  (see protocol_status enum)
//  32      Address      Target address (for selected bus)
//  32      Payload sz   Size of payload in bytes (can be 0)
//
//  ??		[payload]
// ----------------------------------------------------------------------------
// Total 128 bytes + payload

// Packet header
struct protocol_header
{
	u32 magic;			// Always 0xDEADBEEF
	u8  command;
	u8  bus_target;
	u8  data_width;
	u8  status;
	u32 address;
	u32 payload_sz;
};

// Supported commands (v2)
enum protocol_commands
{
	CMD_UNSUPPORTED = 0,
	CMD_ACCESS      = 1
};

// Target bus for commands
enum protocol_bus_type
{
	BUS_UNSUPPORTED = 0,
	BUS_EEPROM      = 1,
	BUS_I2C         = 2,
	BUS_RAW_REG     = 3,	// V5P memory-mapped peripherals
	BUS_RDMA        = 4		// Downstream configuration
};

// Size of data
enum protocol_data_width
{
    WIDTH_UNSUPPORTED = 0,
    WIDTH_BYTE        = 1,	// 8bit
    WIDTH_WORD        = 2,	// 16bit
    WIDTH_LONG        = 3	// 32bit
};

// Status bit bank
enum protocol_status
{
	STATE_UNSUPPORTED = 0,
	STATE_READ        = 1,
	STATE_WRITE       = 2,
	STATE_ACK         = 6,
	STATE_NACK        = 7
};
/* NEW FORMAT - WAIT FOR PYTHON TO BE UPDATED!
 * ALSO: UPDATE CBI/SBI MACROS!
{
	STATE_READ        = 0,
	STATE_WRITE       = 1,
	STATE_ACK         = 2,
	STATE_NACK        = 3,
	STATE_E0          = 4,
	STATE_E1          = 5,
	STATE_E2          = 6,
	STATE_E3          = 7
};
*/

#endif /* PROTOCOL_H_ */
