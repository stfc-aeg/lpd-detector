/**
 * @file protocol.h
 * @author Matt Thorpe, STFC Application Engineering Group
 *
 * TCP sockets protocol for FEM control and configuration
 *
 */

#ifndef PROTOCOL_H_
#define PROTOCOL_H_

#include "xil_types.h"

// Defines
#define MAX_PAYLOAD_SIZE          1024					//!< Maximum payload size (bytes)
#define PROTOCOL_MAGIC_WORD       0xDEADBEEF			//!< Magic word, always the first word in a packet

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
							xil_printf("Stat:  0x%x\r\n",hdr->state); \
							xil_printf("Addr:  0x%x\r\n",hdr->address); \
							xil_printf("Payld: %d\r\n", hdr->payload_sz)
#else
#define DUMPHDR(hdr)
#endif

//! Packet header
struct protocol_header
{
	u32 magic;				//!< Magic word, always 0xDEADBEEF
	u8  command;			//!< Maps to protocol_commands
	u8  bus_target;			//!< Maps to protocol_bus_type
	u8  data_width;			//!< Maps to protocol_data_width
	u8  state;				//!< State byte (R/W/ACK/NACK/Error)
	u32 address;			//!< Target address for command / operation
	u32 payload_sz;			//!< Size of payload on packet, 0 is valid
};

//! Supported commands (v2)
enum protocol_commands
{
	CMD_UNSUPPORTED = 0,	//!< Unsupported command
	CMD_ACCESS      = 1,	//!< Access command (R/W to a FEM bus)
	CMD_INTERNAL	= 2,	//!< Internal command (FEM internal state)
	CMD_ACQUIRE		= 3,	//!< Acquisition command (configure DMA engines)
	CMD_PERSONALITY	= 4		//!< Personality command (handed off to FPM)
};

//! CMD_INTERNAL supported commands
enum internal_commands
{
	CMD_INT_FIRMWARE			= 0,		//!< Reboot to selected firmware
	CMD_INT_GET_HW_INIT_STATE	= 1,		//!< Get hardware init. state
	CMD_INT_WRITE_TO_SYSACE		= 2			//!< Write image to compact flash card via SystemACE
};

//! Target bus for commands
enum protocol_bus_type
{
	BUS_UNSUPPORTED = 0,	//!< Unsupported
	BUS_EEPROM      = 1,	//!< I2C EEPROM
	BUS_I2C         = 2,	//!< I2C bus
	BUS_RAW_REG     = 3,	//!< V5P memory-mapped peripherals
	BUS_RDMA        = 4,	//!< RDMA downstream configuration
	BUS_SPI			= 5,	//!< SPI bus
	BUS_DIRECT		= 6		//!< Direct DDR2 memory write
};

//! Data sizes
enum protocol_data_width
{
    WIDTH_UNSUPPORTED = 0,	//!< Unsupported data width
    WIDTH_BYTE        = 1,	//!< 8-bit
    WIDTH_WORD        = 2,	//!< 16-bit
    WIDTH_LONG        = 3	//!< 32-bit
};

//! Status bit bank
enum protocol_status
{
	STATE_UNSUPPORTED = 0,	//!< Unsupported status
	STATE_READ        = 1,	//!< Read operation
	STATE_WRITE       = 2,	//!	Write operation
	STATE_ACK         = 6,	//!< Acknowledge (ACK)
	STATE_NACK        = 7	//!< No-acknowledge (NACK)
};

// TODO: Make common
//! Acquire mode commands
enum protocol_acq_command
{
	CMD_ACQ_UNSUPPORTED		= 0,	//!< Unsupported command
	CMD_ACQ_CONFIG			= 1,	//!< Configure ready for acquisition
	CMD_ACQ_START			= 2,	//!< Start acquisition
	CMD_ACQ_STOP			= 3,	//!< Stop acquisition
	CMD_ACQ_STATUS			= 4		//!< Report acquisition status
};

// TODO: Make common
//! Acquire mode modes
enum protocol_acq_mode
{
	ACQ_MODE_UNSUPPORTED	= 0,	//!< Unsupported acquisition mode
	ACQ_MODE_NORMAL			= 1,	//!< Arm RX and TX for normal acquisition
	ACQ_MODE_RX_ONLY		= 2,	//!< Arm RX only
	ACQ_MODE_TX_ONLY		= 3,	//!< Arm TX only
	ACQ_MODE_UPLOAD			= 4		//!< Upload upstream configuration
};

//! Acquisition mode parameters
typedef struct
{
	u32 acqMode;					//!< Acquisition mode
	u32 bufferSz;					//!< Buffer size in bytes
	u32 bufferCnt;					//!< Buffer count
	u32 numAcq;						//!< Number of acquisitions expected
	u32 bdCoalesceCount;			//!< Number of RX BDs to process per loop (TX set to x2 this value)
} protocol_acq_config;

// TODO: Make common
//! Acquisition mode state (stored in shared BRAM)
typedef struct
{
	u32 state;						//!< Current state
	u32 bufferCnt;					//!< Number of acquisition buffers allocated
	u32 bufferSize;					//!< Size of acquisition buffers
	u32 readPtr;					//!< Read pointer
	u32 writePtr;					//!< Write pointer
	u32 totalRecv;					//!< Total number of buffers received from I/O Spartans
	u32 totalSent;					//!< Total number of buffers sent to 10GBe DMA channel
	u32 totalErrors;				//!< Total number of DMA errors (do we need to track for each channel?)
} acqStatusBlock;

#endif /* PROTOCOL_H_ */
