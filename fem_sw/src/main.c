/**
 * ----------------------------------------------------------------------------
 * XCAL / LPD FEM prototype embedded platform
 *
 * Matt Thorpe (matt.thorpe@stfc.ac.uk)
 * Application Engineering Department, STFC RAL
 *
 * ----------------------------------------------------------------------------
 *
 * OVERVIEW:
 *
 * Provides Lightweight IP stack on xilkernel platform, supporting a basic
 * remote register read / write functionality and full support for I2C
 * devices (M24C08 8k EEPROM, LM82 monitoring chip) using a simple socket interface.
 *
 * Developed against Xilinx ML507 development board under EDK 13 (Linux)
 *
 * ----------------------------------------------------------------------------
 *
 * Version 1.2 - alpha release not for distribution
 *
 * ----------------------------------------------------------------------------
 *
 * CHANGELOG:
 *
 * 1.1		06-July-2011
 * 	- First functional implementation of FEM communications protocol
 *  - Bug fixes in network select / command processing
 * 1.2		25-July-2011
 *  - RDMA protocol handling implemented
 *  - EEPROM store / retrieve config implemented
 * 1.3		??-Aug-2011
 *  - Refactoring / tidying
 *  - Replaced all xil_printf for DBGOUT macro
 *
 * ----------------------------------------------------------------------------
 *
 * TO DO LIST:
 *
 * TODO: Complete refactoring for AED coding standards adherance
 *
 * TODO: Track down I2C timing issue! (disable DBGOUT?)
 * TODO: Test I2C access via protocol
 * TODO: Replace EEPROM write delay with polling
 *
 * TODO: Support generic EEPROM write access via protocol
 *
 * TODO: Replace uartlite_h with full library, implement read timeouts
 *
 * TODO: Clean network select / command processing logic, make robust
 * TODO: Test with malformed packets, try to break processing loop
 * TODO: Fix pTxPayload fudge in command processing
 * TODO: Make sure return packets <= MAX_PAYLOAD_SIZE
 * TODO: Ensure connection handler observes MAX_CONNECTIONS
 *
 * TODO: Support for concurrent large payload writes
 *
 * TODO: Configure xintc interrupt controller, enable interrupts (will be needed for LM82 ?)
 *
 * TODO: Implement / remove iperf server
 *
 * TODO: Profile memory usage
 * TODO: Tune thread stacksize
 * TODO: Move code to SRAM (REQUIRES FEM!)
 * TODO: Check for memory leaks
 * TODO: Determine why LWIP hangs on init using priority based scheduler
 *
 * TODO: Doxygen comment all functions
 *
 * TODO: Move ML507 specific hardware (GPIO etc) to define block
 *
 * ----------------------------------------------------------------------------
 */



// ----------------------------------------------------------------------------
// Includes
// ----------------------------------------------------------------------------

// Make sure xmk is included first, always!  [XilKernel]
#include "xmk.h"

// Master FEM header file
#include "fem.h"

// General includes
#include "os_config.h"
#include "sys/ksched.h"
#include "sys/init.h"
#include "config/config_param.h"
#include "stdio.h"
#include "xparameters.h"
#include "platform.h"
#include "platform_config.h"
#include <pthread.h>
#include <sys/types.h>
#include <string.h>
#include <stdio.h>

// LWIP includes
#include "lwip/init.h"
#include "lwip/inet.h"
#include "lwip/ip_addr.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include "lwipopts.h"
#include "netif/xadapter.h"

// FEM includes
#include "protocol.h"
#include "rdma.h"
#include "rs232_rdma.h"
#include "gpio.h"
#include "i2c_lm82.h"
#include "i2c_24c08.h"

// iperf
#include "iperf.h"

// EDK hardware includes
#include "xgpio.h"				// TODO: Remove for FEM implementation
#include "xintc.h"
#include "xtmrctr.h"

// Profiling
#include "profile.h"

// Calibrated sleep for MicroBlaze
#include "calib_sleep.h"


// ----------------------------------------------------------------------------
// Defines
// ----------------------------------------------------------------------------

// TODO: Tune these
#define THREAD_STACKSIZE 		4096
#define MAX_CONNECTIONS			4

#define CMD_PORT				6969

#define RDMA_RS232_BASEADDR		XPAR_RS232_UART_2_BASEADDR



// ----------------------------------------------------------------------------
// Function Prototypes
// ----------------------------------------------------------------------------

void* masterThread(void *);			// Main thread launched by xilkernel
void networkManagerThread(void *);	// Sets up LWIP, spawned by master thread
void commandProcessorThread();		// Waits for FEM comms packets, spawned by network manager thread
void commandDispatcher(struct protocol_header* pRxHeader, struct protocol_header *pTxHeader, u8* pRxPayload, u8* pTxPayload);
void testThread();					// Any testing routines go here

int socketRead(int sock, u8* pBuffer, unsigned int numBytes, unsigned int timeoutMs);
void createFailsafeConfig(struct fem_config* pConfig);
void initHardware(void);



// ----------------------------------------------------------------------------
// Global Variable Definitions
// ----------------------------------------------------------------------------

// TODO: Determine what scope this needs and fix it if possible
struct netif server_netif;

// Define our GPIOs on the ML507 dev board (remove for FEM implementation)
// TODO: Remove this for FEM implemtation
XGpio gpioLed8, gpioLed5, gpioDip, gpioSwitches;

XIntc intc;

// TODO: Move to ifdef?
XTmrCtr timer;
struct profiling_results prf;



// ----------------------------------------------------------------------------
// Functions
// ----------------------------------------------------------------------------

int main()
{
    init_platform();

    initHardware();

    xilkernel_init();

    xmk_add_static_thread(masterThread, 0);		// Create the master thread

    xilkernel_start();

    // Never reached
    cleanup_platform();
    
    return 0;
}



// Prints IP address - From XAPP1026
// TODO: Remove
void print_ip(char *msg, struct ip_addr *ip)
{
    print(msg);
    DBGOUT("%d.%d.%d.%d\n\r", ip4_addr1(ip), ip4_addr2(ip), ip4_addr3(ip), ip4_addr4(ip));
}



// Prints network settings - From XAPP1026
// TODO: Remove
void print_ip_settings(struct ip_addr *ip, struct ip_addr *mask, struct ip_addr *gw)
{
    print_ip("    Board IP: ", ip);
    print_ip("    Netmask : ", mask);
    print_ip("    Gateway : ", gw);
}



// Master thread
void* masterThread(void *arg)
{

	sys_thread_t t;

	DBGOUT("\r\n\r\n----------------------------------------------------------------------\r\n");

	// TODO: Why doesn't LWIP initialise if we use SCHED_PRIO?  Is it because we haven't set a thread priority yet?

#if SCHED_TYPE == SCHED_PRIO
    struct sched_param spar;
    DBGOUT("XilMaster: Main thread active, scheduler type is SCHED_PRIO\r\n");
#else
    DBGOUT("XilMaster: Main thread active, scheduler type is SCHED_RR\r\n");
#endif

    // Init LWIP API
    DBGOUT("XilMaster: Initialising LWIP \r\n");
    lwip_init();

    // Spawn LWIP manager thread
    DBGOUT("XilMaster: Spawning network manager thread\r\n");
    t = sys_thread_new("netman", networkManagerThread, NULL, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);
    if (t==NULL) {
    	DBGOUT("XilMaster: sys_thread_new failed!\r\n");
    	return (void*)-1;
    }

    // Nothing to do...
    return (void*)0;
}



// Network manager thread
//
// Configures LWIP and spawns thread to receive packets
void networkManagerThread(void *p)
{

	sys_thread_t t;

	//struct netif server_netif;	// LWIP doesn't work if this is declared here, only in body of main!  Guess scope needs to be wider...
    struct netif *netif;
    struct ip_addr ipaddr, netmask, gateway;

    netif = &server_netif;

    // Get config struct
    // TODO: Move config struct reading to higher level function
    // ----------------------------------------------------------------------------------------------------------------
    struct fem_config femConfig;
    if (readConfigFromEEPROM(0, &femConfig) == -1)
    {
    	DBGOUT("NetMan: Can't get configuration from EEPROM, using failsafe defaults...\r\n");
    	createFailsafeConfig(&femConfig);
    }
    else
    {
    	DBGOUT("NetMan: Got configuration from EEPROM OK!\r\n");
    }

    // Show LM82 setpoints
    DBGOUT("NetMan: LM82 high temp @ %dc\r\n", femConfig.temp_high_setpoint);
    DBGOUT("NetMan: LM82 crit temp @ %dc\r\n", femConfig.temp_crit_setpoint);
    // ----------------------------------------------------------------------------------------------------------------

    // Setup network
    IP4_ADDR(&ipaddr,  femConfig.net_ip[0], femConfig.net_ip[1], femConfig.net_ip[2], femConfig.net_ip[3]);
    IP4_ADDR(&netmask, femConfig.net_nm[0], femConfig.net_nm[1], femConfig.net_nm[2], femConfig.net_nm[3]);
    IP4_ADDR(&gateway, femConfig.net_gw[0], femConfig.net_gw[1], femConfig.net_gw[2], femConfig.net_gw[3]);
    DBGOUT("NetMan: Activating network interface...\r\n");
    print_ip_settings(&ipaddr, &netmask, &gateway);

    // Add network interface to the netif_list, and set it as default
    // NOTE: This can (and WILL) hang forever if the base address for the MAC is incorrect, or not assigned by EDK...
    // (e.g. 0xFFFF0000 etc is invalid).  Use 'Generate Addresses' if this is the case...
    DBGOUT("NetMan: MAC is %02x:%02x:%02x:%02x:%02x:%02x\r\n", femConfig.net_mac[0], femConfig.net_mac[1], femConfig.net_mac[2], femConfig.net_mac[3], femConfig.net_mac[4], femConfig.net_mac[5]);
    if (!xemac_add(netif, &ipaddr, &netmask, &gateway, (unsigned char*)femConfig.net_mac, BADDR_MAC)) {
    	DBGOUT("NetMan: Error adding N/W interface to netif, aborting...\r\n");
        return;
    }
    netif_set_default(netif);

    // Specify that the network if is up
    netif_set_up(netif);

    // Start packet receive thread - required for lwIP operation
    t = sys_thread_new("xemacif_input_thread", (void(*)(void*))xemacif_input_thread, netif, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);
    if (t==NULL)
    {
    	DBGOUT("NetMan: Can't spawn xemacif thread, aborting...\r\n");
    	return;
    }

    // Launch application thread
    t = sys_thread_new("cmd", commandProcessorThread, 0, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);

    // - OR -

    // Launch iperf thread
    //t = sys_thread_new("iperf", iperf_rx_application_thread, 0, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);

    // - OR -

    // Launch testing thread
    t = sys_thread_new("test", testThread, 0, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);

    if (t==NULL)
    {
    	DBGOUT("NetMan: Can't spawn thread, aborting...\r\n");
    }

    //DBGOUT("NetMan: Thread exiting\r\n");
}



// Communicates with PC via TCP/IP socket (SOCK_STREAM) to receive packets
// and display them to stdout (RS232)
//
// TODO: Adhere to MAX_CONNECTIONS
// TODO: Replace return statements, make sure to close any open FDs too
void commandProcessorThread()
{
	// Socket stuff
	int listenerSocket, clientSocket, newFd, addrSize, numFds, numBytesRead, isValid, i;
	struct sockaddr_in serverAddress, clientAddress;
	fd_set readSet, masterSet;
	struct timeval tv;

	// RX and TX packet buffers
	u8* pRxBuffer = (u8*)malloc(sizeof(struct protocol_header)+MAX_PAYLOAD_SIZE);
	u8* pTxBuffer = (u8*)malloc(sizeof(struct protocol_header)+MAX_PAYLOAD_SIZE);
	struct protocol_header* pRxHeader = (struct protocol_header*)pRxBuffer;
	struct protocol_header* pTxHeader = (struct protocol_header*)pTxBuffer;

	//int sockRecvTimeoutMs = 1000;

	// Prepare file descriptor sets
	FD_ZERO(&readSet);
	FD_ZERO(&masterSet);
	numFds = -1;

	// Prepare timeval
	tv.tv_sec = 1;
	tv.tv_usec = 0;

	DBGOUT("CmdProc: Thread starting...\r\n");

	// Open server socket, stream mode
	if ((listenerSocket = lwip_socket(AF_INET, SOCK_STREAM, 0)) < 0)
	{
		DBGOUT("CmdProc: Can't open socket, aborting...\r\n");
		return;
	}

	// Configure socket to receive any incoming connections
	serverAddress.sin_family = AF_INET;
	serverAddress.sin_port = htons(CMD_PORT);
	serverAddress.sin_addr.s_addr = INADDR_ANY;
	memset(&(serverAddress.sin_zero), 0, sizeof(serverAddress.sin_zero));

	// Configure socket (NEW 05/07/11)
	//lwip_setsockopt(listenerSocket, SOL_SOCKET, SO_RCVTIMEO, &sockRecvTimeoutMs, sizeof(sockRecvTimeoutMs) );

	// Bind to address
	if (lwip_bind(listenerSocket, (struct sockaddr *)&serverAddress, sizeof (serverAddress)) < 0)
	{
		DBGOUT("CmdProc: Can't bind to socket %d, aborting...\r\n", CMD_PORT);
		return;
	}

	// Begin listening, register listener as FD of interest to read
	if (lwip_listen(listenerSocket, 5) < 0)
	{
		DBGOUT("CmdProc: Can't listen on socket %d, aborting...\r\n", CMD_PORT);
		return;
	}
	FD_SET(listenerSocket, &masterSet);
	numFds = listenerSocket;

	// ************************* MAIN SERVER LOOP *******************************
	// TODO: Move this somewhere else / split into more functions?  Some deeply-nested logic here!
	while (1) {

		// Copy master set over as readSet will be modified
		memcpy(&readSet, &masterSet, (size_t)sizeof(fd_set));

		isValid = 1;

		// TODO: Use timeval?  (using NULL here means the thread will wait forever without timing out)
		if (lwip_select(numFds + 1, &readSet, NULL, NULL, NULL) == -1)
		{
			// Unrecoverable error
			DBGOUT("CmdProc: Select failed, aborting...\r\n");
			return;
		}

		// Check file descriptors, see which one needs servicing
		for (i=0; i<=numFds; i++)
		{
			if(FD_ISSET(i, &readSet))
			{

				// ----------------------------------------------------------------------------------------------------
				// This is a new connection!
				if (i==listenerSocket)
				{
					DBGOUT("CmdProc: Received new connection!\r\n");

					// Accept connection
					addrSize = sizeof(clientAddress);
					newFd = lwip_accept(listenerSocket, (struct sockaddr*)&clientAddress, (socklen_t*)&addrSize);
					if (newFd == -1)
					{
						// Unrecoverable error
						DBGOUT("CmdProc: Accept error\r\n");
						return;
					}

					// Add to master list of FDs, update count
					FD_SET(newFd, &masterSet);
					if (newFd > numFds)
					{
						numFds = newFd;
					}

				}
				else
				// ----------------------------------------------------------------------------------------------------
				// Existing client is communicating with us
				{

					clientSocket = i;

					// Read header if we can
					//numBytesRead = lwip_read(i, pRxBuffer, sizeof(struct protocol_header));
					numBytesRead = socketRead(i, pRxBuffer, sizeof(struct protocol_header), 0);

					if (numBytesRead < sizeof(struct protocol_header))
					{
						isValid = 0;	// Prevent any further reading of this socket

						if (numBytesRead == 0)
						{
							// Client closed connection, so drop our side
							DBGOUT("CmdProc: Client closed connection.\r\n");
							lwip_close(i);
							FD_CLR(i, &masterSet);
						}
						else if (numBytesRead == -1)
						{
							// Error occurred
							// TODO: get errno?
							DBGOUT("CmdProc: Error encountered during lwip_read(), closing connection.\r\n");
							lwip_close(i);
							FD_CLR(i, &masterSet);
						}
						else
						{
							DBGOUT("CmdProc: Header is smaller than expected (expected %d, got %d)\r\n", sizeof(struct protocol_header), numBytesRead);
						}
					} // END if (numBytesRead < sizeof(struct protocol_header))

					// Everything OK so far, validate magic...
					if ((pRxHeader->magic != PROTOCOL_MAGIC_WORD) && (isValid==1))
					{
						DBGOUT("CmdProc: Got bad packet, ignoring... (magic=%x)\r\n", pRxHeader->magic);
						isValid = 0;
					}

					// If header looks to be well formed, process it's contents
					if (isValid==1) {

						// DEBUG - dump out header
						DBGOUT("------------------------\r\n");
						DBGOUT("HEADER:\r\n");
						DUMPHDR(pRxHeader);
						DBGOUT("------------------------\r\n");

						// --------------------- BEGIN READING VALID PACKET ----------------------

						if (pRxHeader->command == CMD_ACCESS) {

							// TODO: Verify payload_sz%data_width == 0!

							if (pRxHeader->payload_sz>0 && pRxHeader->payload_sz <= MAX_PAYLOAD_SIZE)
							{
								//numBytesRead = lwip_read(i, pRxBuffer+sizeof(struct protocol_header), pRxHeader->payload_sz);
								numBytesRead = socketRead(i, pRxBuffer+sizeof(struct protocol_header), pRxHeader->payload_sz, 0);
								if (numBytesRead < pRxHeader->payload_sz)
								{
									// Prevent further processing because payload is smaller than expected
									isValid = 0;

									if (numBytesRead == 0)
									{
										// TODO: Fix this, drops connection if we receive a header but no payload.  What should we do in that case?
										// Client closed connection, so drop our side
										DBGOUT("CmdProc: Client closed connection (payload processing stage).\r\n");
										lwip_close(i);
										FD_CLR(i, &masterSet);
									}
									else if (numBytesRead == -1)
									{
										// Error occurred
										// TODO: get errno?
										DBGOUT("CmdProc: Error encountered during lwip_read(), closing connection.\r\n");
										lwip_close(i);
										FD_CLR(i, &masterSet);
									}
									else
									{
										// Got less data than expected
										DBGOUT("CmdProc: Payload is smaller than expected (expected %d, got %d)\r\n", pRxHeader->payload_sz, numBytesRead);
									}

								} else {

									// Received payload OK, correct size
									DBGOUT("PAYLOAD:\r\n");
									DBGOUT("[sz=%d] = ", pRxHeader->payload_sz);
									for(i=0; i<pRxHeader->payload_sz; i++)
									{
										DBGOUT("%x ",pRxBuffer[i+sizeof(struct protocol_header)]);
									}
									DBGOUT("\r\n");
									DBGOUT("------------------------\r\n");
								}
							}
							else
							{
								DBGOUT("CmdProc: No payload to recover...\r\n");
							} // END if (header.payloadSize>0))

						} // END if (rx_header.command == CMD_ACCESS)

						// ------------------- END READING VALID PACKET ----------------------

					} // END if isValid==1)

					// Process command if we encountered no errors
					if (isValid==1)
					{

						// Kludge new vars into old prototype!
						// TODO: Update command_dispatcher function prototype
						commandDispatcher(pRxHeader, pTxHeader, pRxBuffer+sizeof(struct protocol_header), pTxBuffer+sizeof(struct protocol_header));

						if (lwip_send(clientSocket, pTxBuffer, sizeof(struct protocol_header) + pTxHeader->payload_sz, 0) == -1)
						{
							DBGOUT("CmdProc: Error sending response packet!\r\n");
						}

					}

				}	// END else clause

			}	// END FD_ISSET(i)

		}	// END for (fd)

	}	// END infinite while
	// *********************** END MAIN SERVER LOOP *****************************

	// Code below here will never run...  but just in case output debug message
	DBGOUT("CmdProc: Exiting thread! [SHOULD NEVER EXECUTE!]\r\n");

}



// New protocol command dispatcher
// Note: it is assumed that the packet is well formed before by it being passed to this function
// Also command processor thread means that command == CMD_ACCESS, the only currently supported command ;)
void commandDispatcher(struct protocol_header* pRxHeader,
                        struct protocol_header* pTxHeader,
                        u8* pRxPayload,
                        u8* pTxPayload)
{

	int i;					// General use variable
	int data_width = 0;
	int response_sz = 0;	// Payload size for response packet (IN BYTES)
	u8 status = 0;			// Status byte

	// Native size pointers for various data widths
	//u8*  pTxPayload_8	= NULL;
	//u16* pTxPayload_16	= NULL;
	u32* pTxPayload_32  = NULL;
	u32* pRxPayload_32  = NULL;

	// Copy original header to response packet, take a local copy of the status byte to update
	memcpy(pTxHeader, pRxHeader, sizeof(struct protocol_header));
	status = pRxHeader->status;

	// Set first 32bit int in payload to be number of operations performed
	pRxPayload_32 = (u32*)pRxPayload;
	pTxPayload_32 = (u32*)pTxPayload;
	if (CMPBIT(status, STATE_READ))
	{
		// First (only) 32bit int of payload is # ops, copy it to response packet
		*pTxPayload_32 = *pRxPayload_32;
	}
	else if (CMPBIT(status, STATE_WRITE))
	{
		// Calculate # ops
		// TODO: STOP CHEATING
		*pTxPayload_32 = 1;
		/*
		switch(pRxHeader->data_width)
		{
		case WIDTH_BYTE:
			*pTxPayload_32 =
			break;
		case WIDTH_WORD:
			*pTxPayload_32 =
			break;
		case WIDTH_LONG:
			*pTxPayload_32 =
			break;
		}
		*/
	}
	else
	{
		// Neither write nor read requested, can't process so just return error response
		DBGOUT("CmdDisp: Invalid operation\r\n");
		SBIT(status, STATE_NACK);
		// TODO: Set error bits
		pTxHeader->status = status;
		pTxHeader->payload_sz = 0;
		return;
	}

	response_sz += sizeof(u32);

	// Process packet based on target
	switch(pRxHeader->bus_target)
	{

		// TODO: Remove BUS_GPIO target
		// --------------------------------------------------------------------
		case BUS_GPIO:
			SBIT(status, STATE_NACK);	// Not going to implement.
			break; // BUS_GPIO

		// --------------------------------------------------------------------
		case BUS_I2C:

			// Verify request parameters are sane
			if ( (pRxHeader->data_width != WIDTH_BYTE) || ( pRxHeader->status == STATE_READ && (pRxHeader->payload_sz != sizeof(u32)) ) )
			{
				DBGOUT("CmdDisp: Invalid request (BUS=0x%x, WDTH=0x%x, STAT=0x%x, PYLDSZ=0x%x)\r\n", pRxHeader->bus_target, pRxHeader->data_width, pRxHeader->status, pRxHeader->payload_sz);
				SBIT(status, STATE_NACK);
				// TODO: Set error bits
				break;
			}
			data_width = sizeof(u8);	// All I2C operations are byte level

			if (CMPBIT(status, STATE_READ))
			{
				i = readI2C(pRxHeader->address, pTxPayload + 1, (u32)pRxPayload[0]);
				if (i != (u32)pRxPayload[0])
				{
					// I2C operation failed, set NACK
					SBIT(status, STATE_NACK);
					// TODO: Set error bits?
				}
				else
				{
					// Set ACK, payload size
					SBIT(status, STATE_ACK);
					response_sz += i;
				}

			}
			else if (CMPBIT(status, STATE_WRITE))
			{
				i = writeI2C(pRxHeader->address, pRxPayload, pRxHeader->payload_sz);
				if (i != pRxHeader->payload_sz)
				{
					// I2C operation failed, set NACK
					SBIT(status, STATE_NACK);
					// TODO: Set error bits?
				}
				else
				{
					// Set ACK
					SBIT(status, STATE_ACK);
				}
			}
			else
			{
				// Neither R or W bits set, can't process request
				DBGOUT("CmdDisp: Error, can't determine BUS_I2C operation mode, status was 0x%x\r\n", status);
				// TODO: Set error bits
			}

			break; // BUS_I2C

		// --------------------------------------------------------------------
		case BUS_RAW_REG:

			// Verify request parameters are sane
			// We don't support anything other than 32-bit operations for RAW_REG as all Xilinx registers are 32bit.
			if ( (pRxHeader->data_width != WIDTH_LONG) || ( pRxHeader->status == STATE_READ && (pRxHeader->payload_sz != sizeof(u32)) ) )
			{
				DBGOUT("CmdDisp: Invalid request (BUS=0x%x, WDTH=0x%x, STAT=0x%x, PYLDSZ=0x%x)\r\n", pRxHeader->bus_target, pRxHeader->data_width, pRxHeader->status, pRxHeader->payload_sz);
				SBIT(status, STATE_NACK);
				// TODO: Set error bits
				break;
			}

			data_width = sizeof(u32);
			pTxPayload_32 = (u32*)(pTxPayload+response_sz);

			if (CMPBIT(status, STATE_READ)) // READ OPERATION
			{

				// DEBUG - Prove to myself that register reads are 32bit (truncated in the case of GPIO_LED as unused signals discarded by synthesis)
				//DBGOUT("DEBUG: 0x%x\r\n", readRegister_32(BADDR_MAC+0x2C));		// TEMAC RDY0 register, non zero on reset!

				pRxPayload_32 = (u32*)pRxPayload;
				for (i=0; i<*pRxPayload_32; i++)
				{
					DBGOUT("CmdDisp: Read ADDR 0x%x", pRxHeader->address + (i*data_width));
					*(pTxPayload_32+i) = readRegister_32(pRxHeader->address + (i*data_width));
					DBGOUT(" VALUE 0x%x\r\n", readRegister_32(pRxHeader->address + (i*data_width)));
					response_sz += data_width;
				}
				SBIT(status, STATE_ACK);

			}
			else if (CMPBIT(status, STATE_WRITE)) // WRITE OPERATION
			{
				for (i=0; i<((pRxHeader->payload_sz)/data_width); i++)
				{
					pRxPayload_32 = (u32*)pRxPayload;
					DBGOUT("CmdDisp: Write ADDR 0x%x VALUE 0x%x\r\n", pRxHeader->address + (i*data_width), *(pRxPayload_32+i));
					writeRegister_32( pRxHeader->address + (i*data_width), *(pRxPayload_32+i) );
				}
				SBIT(status, STATE_ACK);
			}
			else
			{
				// Neither R or W bits set, can't process request
				DBGOUT("CmdDisp: Error, can't determine BUS_RAW_REG operation mode, status was 0x%x\r\n", status);

				SBIT(status, STATE_NACK);
				// TODO: Set error bits
			}

			break; // BUS_RDMA

		// --------------------------------------------------------------------
		case BUS_RDMA:

			// Verify request parameters are sane
			// We don't support anything other than 32-bit operations for RAW_REG as all RDMA registers are 32bit.
			if ( (pRxHeader->data_width != WIDTH_LONG) || ( pRxHeader->status == STATE_READ && (pRxHeader->payload_sz != sizeof(u32)) ) )
			{
				DBGOUT("CmdDisp: Invalid request (BUS=0x%x, WDTH=0x%x, STAT=0x%x, PYLDSZ=0x%x)\r\n", pRxHeader->bus_target, pRxHeader->data_width, pRxHeader->status, pRxHeader->payload_sz);
				SBIT(status, STATE_NACK);
				// TODO: Set error bits
				break;
			}

			data_width = sizeof(u32);
			pTxPayload_32 = (u32*)(pTxPayload+response_sz);

			if (CMPBIT(status, STATE_READ)) // READ OPERATION
			{

				pRxPayload_32 = (u32*)pRxPayload;
				for (i=0; i<*pRxPayload_32; i++)
				{
					DBGOUT("CmdDisp: Read ADDR 0x%x", pRxHeader->address + (i*data_width));
					*(pTxPayload_32+i) = readRdma(RDMA_RS232_BASEADDR, pRxHeader->address + i, &timer, &prf);
					DBGOUT(" VALUE 0x%x\r\n", readRegister_32(pRxHeader->address + i));
					response_sz += data_width;
				}
				SBIT(status, STATE_ACK);

			}
			else if (CMPBIT(status, STATE_WRITE)) // WRITE OPERATION
			{
				for (i=0; i<((pRxHeader->payload_sz)/data_width); i++)
				{
					pRxPayload_32 = (u32*)pRxPayload;
					DBGOUT("CmdDisp: Write ADDR 0x%x VALUE 0x%x\r\n", pRxHeader->address + i, *(pRxPayload_32+i));
					writeRdma(RDMA_RS232_BASEADDR, pRxHeader->address + i, *(pRxPayload_32+i), &timer, &prf);
				}
				SBIT(status, STATE_ACK);
			}
			else
			{
				// Neither R or W bits set, can't process request
				DBGOUT("CmdDisp: Error, can't determine BUS_RDMA operation mode, status was 0x%x\r\n", status);

				SBIT(status, STATE_NACK);
				// TODO: Set error bits
			}

			// TODO: Remove or move to ifdef
			// Display profiling information
			//DBGOUT("CmdDisp: Operation took %d ticks (first byte send took %d)\r\n", prf.data2, prf.data1);


			break; // BUS_RAW_REG

		case BUS_UNSUPPORTED:
		default:
			SBIT(status, STATE_NACK);
			// TODO: Set error bits
			break;

	}

	// Build response header (all fields other status byte stay same as received packet)
	pTxHeader->status = status;
	pTxHeader->payload_sz = response_sz;

}



// This method only being used while testing, will remove soon
// PUT ALL TESTING CODE IN THIS METHOD!
void testThread()
{

	DBGOUT("TEST: Entered test function!\r\n");

	/*
	// *** For LM82 tests ***
	int localTemp = 0;
	int remoteTemp = 0;
	u8 cmd = LM82_REG_READ_STATUS;
	u8 stat = 0;
	*/

	// *** For EEPROM tests ***
/*
	int i;
	u8 readBuffer[8192];
	u8 dummyData[] = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,
					  16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,
					  32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,
					  48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63};

	// Test patterns for EEPROM write
	u8 blankData[] = {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF};
	//u8 blankData[] = {0xA5,0x5A,0xA5,0x5A,0xA5,0x5A,0xA5,0x5A,0xA5,0x5A,0xA5,0x5A,0xA5,0x5A,0xA5,0x5A};
	//u8 blankData[] = {0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F};
*/

	// Initalise LM82 device with setpoints we can easily trigger
	//DBGOUT("TEST: Configuring LM82 device... ");
	//initLM82(29,32);		// (warn temp, crit temp)
	//DBGOUT("OK!\r\n");

	// ------------------------------------------------------------------------
	// LM82 tester
	/*
	while (1)
	{
		sleep(10000);
		remoteTemp = readRemoteTemp();
		localTemp = readLocalTemp();
		writeI2C(IIC_ADDRESS_TEMP, &cmd, 1);
		readI2C(IIC_ADDRESS_TEMP, &stat, 1);
		DBGOUT("Test:  Local LM82 temp: %dc\r\n", localTemp);
		DBGOUT("Test: Remote LM82 temp: %dc\r\n", remoteTemp);
		DBGOUT("Test:  Status register: 0x%x\r\n", stat);
	}
	*/

	// ------------------------------------------------------------------------
	// EEPROM tester

	/*
	usleep(2000);

	// Blank out first 8 pages for testing
	for (i=0; i<8; i++)
	{
		writeToEEPROM((i*16), blankData, 16);
	}

	// Do test write
	writeToEEPROM(7, dummyData, 34);

	// Do readback to check data
	DBGOUT("----------------------\r\n");
	readFromEEPROM(0, readBuffer, 8192);
	for (i=0; i<16; i++)
	{
		// sooo ugly :(
		if (i==0) { DBGOUT("00"); }
		DBGOUT("%x: %x %x %x %x %x %x %x %x   %x %x %x %x %x %x %x %x \r\n",
			(i*16)*16, readBuffer[(i*16)+0], readBuffer[(i*16)+1], readBuffer[(i*16)+2], readBuffer[(i*16)+3], readBuffer[(i*16)+4], readBuffer[(i*16)+5], readBuffer[(i*16)+6], readBuffer[(i*16)+7],
			readBuffer[(i*16)+8], readBuffer[(i*16)+9], readBuffer[(i*16)+10], readBuffer[(i*16)+11], readBuffer[(i*16)+12], readBuffer[(i*16)+13], readBuffer[(i*16)+14], readBuffer[(i*16)+15] );
	}
	*/

	// ------------------------------------------------------------------------
	// Rob RDMA / RS232 link test

	/*
	DBGOUT("Test: Running RDMA test ...\r\n");
	u32 addr;
	u32 regVal = 0;

	// Read read-only register
	addr = 4;
	regVal = readRdma(RDMA_RS232_BASEADDR, addr);
	DBGOUT("Test: RO:RDMA register 0x%x = 0x%x\r\n", addr, regVal);

	// Read read-write register
	addr = 1;
	regVal = readRdma(RDMA_RS232_BASEADDR, addr);
	DBGOUT("Test: RW:RDMA register 0x%x = 0x%x\r\n", addr, regVal);

	// Write read-write register
	u32 testValue = 0xDEADBEEF;
	writeRdma(RDMA_RS232_BASEADDR, addr, testValue);
	DBGOUT("Test: Wrote 0x%x to 0x%x\r\n", addr, testValue);

	// Read read-write register
	regVal = readRdma(RDMA_RS232_BASEADDR, addr);
	DBGOUT("Test: RW:RDMA register 0x%x = 0x%x\r\n", addr, regVal);

	// Don't let EEPROM tests run!
	return;
	*/

	// ------------------------------------------------------------------------
	// FEM configuration struct test
	DBGOUT("TEST: Running EEPROM struct test...\r\n");
	struct fem_config cfg;		// Used to write to EEPROM
	struct fem_config test;		// Read back from EEPROM

	// Make a dummy struct
	createFailsafeConfig(&cfg);

	// Write to EEPROM
	DBGOUT("TEST: Writing EEPROM struct...\r\n");
	writeToEEPROM(0, (u8*)&cfg, sizeof(struct fem_config));

	// Read back
	DBGOUT("TEST: Reading EEPROM struct...\r\n");
	readFromEEPROM(0, (u8*) &test, sizeof(struct fem_config));

	// Test values
	// NOTE: THIS DOES NOT TEST ALL PARAMS!
	int numErrors = 0;
	if (test.net_mac[0] != cfg.net_mac[0]) { DBGOUT("EEPROM: mac_address[0] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[0], test.net_mac[0]); numErrors++; }
	if (test.net_mac[1] != cfg.net_mac[1]) { DBGOUT("EEPROM: mac_address[1] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[1], test.net_mac[1]); numErrors++; }
	if (test.net_mac[2] != cfg.net_mac[2]) { DBGOUT("EEPROM: mac_address[2] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[2], test.net_mac[2]); numErrors++; }
	if (test.net_mac[3] != cfg.net_mac[3]) { DBGOUT("EEPROM: mac_address[3] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[3], test.net_mac[3]); numErrors++; }
	if (test.net_mac[4] != cfg.net_mac[4]) { DBGOUT("EEPROM: mac_address[4] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[4], test.net_mac[4]); numErrors++; }
	if (test.net_mac[5] != cfg.net_mac[5]) { DBGOUT("EEPROM: mac_address[5] differs! (Should be 0x%x, got 0x%x)\r\n", cfg.net_mac[5], test.net_mac[5]); numErrors++; }
	if (test.temp_high_setpoint != cfg.temp_high_setpoint) { DBGOUT("EEPROM: temp_high_setpoint differs! (Should be 0x%x, got 0x%x)\r\n", cfg.temp_high_setpoint, test.temp_high_setpoint); numErrors++; }
	if (test.temp_crit_setpoint != cfg.temp_crit_setpoint) { DBGOUT("EEPROM: temp_crit_setpoint differs! (Should be 0x%x, got 0x%x)\r\n", cfg.temp_crit_setpoint, test.temp_crit_setpoint); numErrors++; }
	if (test.sw_major_version != cfg.sw_major_version) { DBGOUT("EEPROM: sw_major_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.sw_major_version, test.sw_major_version); numErrors++; }
	if (test.sw_minor_version != cfg.sw_minor_version) { DBGOUT("EEPROM: sw_minor_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.sw_minor_version, test.sw_minor_version); numErrors++; }
	if (test.fw_major_version != cfg.fw_major_version) { DBGOUT("EEPROM: fw_major_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.fw_major_version, test.fw_major_version); numErrors++; }
	if (test.fw_minor_version != cfg.fw_minor_version) { DBGOUT("EEPROM: fw_minor_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.fw_minor_version, test.fw_minor_version); numErrors++; }
	if (test.hw_major_version != cfg.hw_major_version) { DBGOUT("EEPROM: hw_major_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.hw_major_version, test.hw_major_version); numErrors++; }
	if (test.hw_minor_version != cfg.hw_minor_version) { DBGOUT("EEPROM: hw_minor_version differs! (Should be 0x%x, got 0x%x)\r\n", cfg.hw_minor_version, test.hw_minor_version); numErrors++; }
	if (test.board_id != cfg.board_id) { DBGOUT("EEPROM: board_id differs! (Should be 0x%x, got 0x%x)\r\n", cfg.board_id, test.board_id); numErrors++; }
	if (test.board_type != cfg.board_type) { DBGOUT("EEPROM: board_id differs! (Should be 0x%x, got 0x%x)\r\n", cfg.board_type, test.board_type); numErrors++; }
	if (numErrors >0 )
	{
		DBGOUT("TEST: EEPROM struct readback encountered %d error(s)\r\n", numErrors);
	}
	else
	{
		DBGOUT("TEST: EEPROM struct readback test OK!\r\n");
	}

	// Do readback to check data
	u8 readBuffer[sizeof(struct fem_config)];
	int i;
	readFromEEPROM(0, readBuffer, sizeof(struct fem_config));
	DBGOUT("----------------------\r\n");
	for (i=0; i<16; i++)
	{
		// sooo ugly :(
		if (i==0) { DBGOUT("00"); }
		DBGOUT("%x: %x %x %x %x %x %x %x %x   %x %x %x %x %x %x %x %x \r\n",
			(i*16)*16, readBuffer[(i*16)+0], readBuffer[(i*16)+1], readBuffer[(i*16)+2], readBuffer[(i*16)+3], readBuffer[(i*16)+4], readBuffer[(i*16)+5], readBuffer[(i*16)+6], readBuffer[(i*16)+7],
			readBuffer[(i*16)+8], readBuffer[(i*16)+9], readBuffer[(i*16)+10], readBuffer[(i*16)+11], readBuffer[(i*16)+12], readBuffer[(i*16)+13], readBuffer[(i*16)+14], readBuffer[(i*16)+15] );
	}

	DBGOUT("Test: Thread exiting.\r\n");
}



// Reads the specified number of bytes from the given socket within the timeout period or returns an error code
// TODO: Move to FEM support library
int socketRead(int sock, u8* pBuffer, unsigned int numBytes, unsigned int timeoutMs)
{
	// TODO: Use timeoutMs, remove maxloops
	int totalBytes = 0;
	int read = 0;

	int tempNumLoops = 0;
	int tempMaxLoops = 100;

	while (totalBytes < numBytes)
	{
		read = lwip_read(sock, (void*)pBuffer, numBytes-read);
		if (read==0) {
			// Client closed connection
			return 0;
		}
		else if (read!=-1)
		{
			totalBytes += read;
		}
		if (tempNumLoops++ == tempMaxLoops)
		{
			// Break out
			DBGOUT("socketRead: Hit maximum retries, bailing out...\r\n");
			return -1;
		}

	}

	//DBGOUT("better_read: Took %d loops to get %d bytes!\r\n", tempNumLoops, numBytes);
	return totalBytes;
}



// Creates failsafe default config object, used in case EEPROM config is not valid or missing
// TODO: Move to FEM support library?
void createFailsafeConfig(struct fem_config* pConfig)
{
	pConfig->header				= EEPROM_MAGIC_WORD;

	// MAC address
	pConfig->net_mac[0]			= 0x00;
	pConfig->net_mac[1]			= 0x0A;
	pConfig->net_mac[2]			= 0x35;
	pConfig->net_mac[3]			= 0x00;
	pConfig->net_mac[4]			= 0xBE;
	pConfig->net_mac[5]			= 0xEF;

	// IP address
	pConfig->net_ip[0]			= 192;
	pConfig->net_ip[1]			= 168;
	pConfig->net_ip[2]			= 1;
	pConfig->net_ip[3]			= 10;

	// Netmask
	pConfig->net_nm[0]			= 255;
	pConfig->net_nm[1]			= 255;
	pConfig->net_nm[2]			= 255;
	pConfig->net_nm[3]			= 0;

	// Default gateway
	pConfig->net_gw[0]			= 192;
	pConfig->net_gw[1]			= 168;
	pConfig->net_gw[2]			= 1;
	pConfig->net_gw[3]			= 1;

	// LM82 setpoints
	pConfig->temp_high_setpoint	= 40;
	pConfig->temp_crit_setpoint	= 75;

	// Software revision
	pConfig->sw_major_version	= 1;
	pConfig->sw_minor_version	= 2;

	// Firmware revision
	pConfig->fw_major_version	= 1;
	pConfig->fw_minor_version	= 0;

	// Hardware revision
	pConfig->hw_major_version	= 1;
	pConfig->hw_minor_version	= 0;

	// Board ID
	pConfig->board_id			= 1;
	pConfig->board_type			= 1;

}

// Initialises xilinx EDK hardware
// TODO: How should we return if something didn't initialise properly?  Status code + error string?
void initHardware(void)
{

	int status;

	// ------------------------------------------------------------------------
    // Initialise GPIO devices
    // TODO: Remove once code is moved to FEM board
    if (initGpioDevices(&gpioLed8, &gpioLed5, &gpioDip, &gpioSwitches) == -1)
    {
    	DBGOUT("initHardware: Failed to initialise GPIOs.\r\n");
    }
    // ------------------------------------------------------------------------



    // ------------------------------------------------------------------------
    // Initialise timer
    // Timer will give results in CPU ticks, so use XPAR_CPU_PPC440_CORE_CLOCK_FREQ_HZ :)
    status = XTmrCtr_Initialize(&timer, XPAR_XPS_TIMER_0_DEVICE_ID);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to initialise timer.\r\n");
    }
    // ------------------------------------------------------------------------

    // ------------------------------------------------------------------------
    // Calibrate usleep
    // On PPC usleep is implemented using the CPU time base register but on
    // MicroBlaze we need to do this ourselves using the timer.
    status = calibrateSleep(&timer);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to calibrate sleep.\r\n");
    }
    // ------------------------------------------------------------------------

    // ------------------------------------------------------------------------
    // Initialise and configure interrupt controller
    status = XIntc_Initialize(&intc, XPAR_XPS_INTC_0_DEVICE_ID);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to initialise interrupt controller.\r\n");
    }
    status = XIntc_Start(&intc, XIN_REAL_MODE);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to start interrupt controller.\r\n");
    }
    // ------------------------------------------------------------------------

    // ------------------------------------------------------------------------
    // Show serial port info
    if (XPAR_RS232_UART_1_BAUDRATE != XPAR_UARTLITE_0_BAUDRATE)
    {
    	DBGOUT("XilMaster: UART1 baud discrepancy (%d, %d)\r\n", XPAR_RS232_UART_1_BAUDRATE, XPAR_UARTLITE_0_BAUDRATE);
    }
    else
    {
    	DBGOUT("XilMaster: UART1 (Debug) @ %d\r\n", XPAR_RS232_UART_1_BAUDRATE);
    }

    if (XPAR_RS232_UART_2_BAUDRATE != XPAR_UARTLITE_1_BAUDRATE)
    {
    	DBGOUT("XilMaster: UART2 baud discrepancy (%d, %d)\r\n", XPAR_RS232_UART_2_BAUDRATE, XPAR_UARTLITE_1_BAUDRATE);
    }
    else
    {
    	DBGOUT("XilMaster: UART2 (RDMA)  @ %d\r\n", XPAR_RS232_UART_2_BAUDRATE);
    }
    // ------------------------------------------------------------------------

}

