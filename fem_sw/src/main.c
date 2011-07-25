/**
 * XCAL / LPD FEM prototype embedded platform
 *
 * Matt Thorpe (matt.thorpe@stfc.ac.uk)
 * Application Engineering Department, STFC RAL
 *
 * Provides Lightweight IP stack on xilkernel platform, supporting a basic
 * remote register read / write functionality and full support for I2C
 * devices (M24C08 8k EEPROM, LM82 monitoring chip) using a simple socket interface.
 *
 * Developed against Xilinx ML507 development board under EDK 12.1 (windows)
 *
 * Version 1.1 - alpha release not for distribution
 *
 * -
 *
 * CHANGELOG:
 *
 * 1.1		06-July-2011
 * 	- First functional implementation of FEM communications protocol
 *  - Bug fixes in network select / command processing
 *
 * -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
 * TODO: Clean network select / command processing logic, make robust
 *
 * TODO: Implement configuration structure, store in EEPROM
 * TODO: Read configuration structure, use to configure board
 * TODO: Configure xintc interrupt controller, enable interrupts (will be needed for LM82)
 *
 * TODO: Implement memory self-test (use xil_testmem.h, use caution this is a destructive test!)
 *
 * TODO: Tune thread stacksize
 * TODO: Profile memory usage
 * TODO: Check for memory leaks
 * TODO: Determine why LWIP hangs on init using priority based scheduler
 *
 * TODO: Reformat code, remove debugging (xil_printf) calls
 * TODO: Doxygen comment all functions
 * TODO: Remove GPIO handles when porting to FEM hardware
 *
 * -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
 */

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

// GPIO include
#include "xgpio.h"

// Xilinx memory testing
// TODO: Get John's PPC running memory check!
//#include "xil_testmem.h"

// iperf
#include "iperf.h"

// FEM includes
#include "protocol.h"
#include "rdma.h"
#include "rs232_rdma.h"
#include "gpio.h"
#include "i2c_lm82.h"
#include "i2c_24c08.h"

// TODO: Tune these
#define THREAD_STACKSIZE 		4096
#define MAX_CONNECTIONS			4

#define CMD_PORT				6969

#define RDMA_RS232_BASEADDR		XPAR_RS232_UART_2_BASEADDR

// Function prototypes
void* master_thread(void *);			// Main thread launched by xilkernel
void network_manager_thread(void *);	// Sets up LWIP, spawned by master thread
void command_processor_thread();		// Waits for FEM comms packets, spawned by network manager thread
void command_dispatcher(struct protocol_header* pRxHeader, struct protocol_header *pTxHeader, u8* pRxPayload, u8* pTxPayload);
void test_thread();						// Any testing routines go here
int better_read(int sock, u8* pBuffer, unsigned int numBytes, unsigned int timeoutMs);

// TODO: Determine what scope this needs and fix it if possible
struct netif server_netif;

// Define our GPIOs on the ML507 dev board (remove for FEM implementation)
// TODO: Remove this
XGpio GpioLed8, GpioLed5, GpioDip, GpioSwitches;

// RDMA base addresses for EDK peripherals (provide a way to query these from protocol?)
u64 rdmaLocations[] =	{
							XPAR_DIP_SWITCHES_8BIT_BASEADDR,
							XPAR_LEDS_8BIT_BASEADDR,
							XPAR_LEDS_POSITIONS_BASEADDR,
							XPAR_PUSH_BUTTONS_5BIT_BASEADDR,
							//XPAR_HARD_ETHERNET_MAC_CHAN_0_BASEADDR,   // Bad idea!
							XPAR_IIC_EEPROM_BASEADDR,
							//XPAR_RS232_UART_1_BASEADDR				// Bad idea!
						};

// Functions
int main()
{
    init_platform();

    // Init GPIO devices
    // TODO: Remove once code is moved to FEM board
    if (initGpioDevices(&GpioLed8, &GpioLed5, &GpioDip, &GpioSwitches) == -1)
    {
    	xil_printf("ERROR during gpio init!\r\n");
    }

    xilkernel_init();

    xmk_add_static_thread(master_thread, 0);		// Create the master thread

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
    xil_printf("%d.%d.%d.%d\n\r", ip4_addr1(ip), ip4_addr2(ip), ip4_addr3(ip), ip4_addr4(ip));
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
void* master_thread(void *arg)
{

	sys_thread_t t;

	xil_printf("\r\n\r\n----------------------------------------------------------------------\r\n");

	// TODO: Why doesn't LWIP initialise if we use SCHED_PRIO?  Is it because we haven't set a thread priority yet?

#if SCHED_TYPE == SCHED_PRIO
    struct sched_param spar;
    xil_printf("XilMaster: Main thread active, scheduler type is SCHED_PRIO\r\n");
#else
    xil_printf("XilMaster: Main thread active, scheduler type is SCHED_RR\r\n");
#endif

    // Init LWIP API
    xil_printf("XilMaster: Initialising LWIP \r\n");
    lwip_init();

    // Spawn LWIP manager thread
    xil_printf("XilMaster: Spawning network manager thread\r\n");
    t = sys_thread_new("netman", network_manager_thread, NULL, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);
    if (t==NULL) {
    	xil_printf("XilMaster: sys_thread_new failed!\r\n");
    	return (void*)-1;
    }

    // Nothing to do...
    return (void*)0;
}


// Network manager thread
//
// Configures LWIP and spawns thread to receive packets
void network_manager_thread(void *p)
{

	sys_thread_t t;

	//struct netif server_netif;	// LWIP doesn't work if this is declared here, only in body of main!  Guess scope needs to be wider...
    struct netif *netif;
    struct ip_addr ipaddr, netmask, gw;

    // MAC address
    // TODO: Set ethernet MAC address from EEPROM
    unsigned char mac_ethernet_address[] = { 0x00, 0x0a, 0x35, 0x00, 0x01, 0x02 };

    netif = &server_netif;

    xil_printf("NetMan: Starting up...\r\n");

    // IP addresses
    // TODO: Set ethernet IP / netmask / gateway from EEPROM
    IP4_ADDR(&ipaddr,  192, 168,   1, 10);
    IP4_ADDR(&netmask, 255, 255, 255,  0);
    IP4_ADDR(&gw,      192, 168,   1,  1);
    xil_printf("NetMan: Activating network interface:\r\n");
    print_ip_settings(&ipaddr, &netmask, &gw);
    xil_printf("NetMan: MAC is %02x:%02x:%02x:%02x:%02x\r\n", mac_ethernet_address[0], mac_ethernet_address[1], mac_ethernet_address[2], mac_ethernet_address[3], mac_ethernet_address[4]);

    // Add network interface to the netif_list, and set it as default
    // NOTE: This can (and WILL) hang forever if the base address for the MAC is incorrect, or not assigned by EDK... (e.g. 0xFFFF0000 etc is invalid).
    // Use 'Generate Addresses' if this is the case...
    xil_printf("NetMan: Base address = %x\r\n", BADDR_MAC);
    if (!xemac_add(netif, &ipaddr, &netmask, &gw, mac_ethernet_address, BADDR_MAC)) {
        xil_printf("NetMan: Error adding N/W interface to netif, aborting...\r\n");
        return;
    }
    netif_set_default(netif);

    // Specify that the network if is up
    netif_set_up(netif);

    // Start packet receive thread - required for lwIP operation
    t = sys_thread_new("xemacif_input_thread", (void(*)(void*))xemacif_input_thread, netif, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);
    if (t==NULL)
    {
    	xil_printf("NetMan: Can't spawn xemacif thread, aborting...\r\n");
    	return;
    }

    // Launch application thread
    //t = sys_thread_new("cmd", command_processor_thread, 0, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);

    // - OR -

    // Launch iperf thread
    //t = sys_thread_new("iperf", iperf_rx_application_thread, 0, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);

    // - OR -

    // Launch testing thread
    t = sys_thread_new("test", test_thread, 0, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);

    if (t==NULL)
    {
    	xil_printf("NetMan: Can't spawn thread, aborting...\r\n");
    }

    //xil_printf("NetMan: Thread exiting\r\n");
}



// Communicates with PC via TCP/IP socket (SOCK_STREAM) to receive packets
// and display them to stdout (RS232)
//
// TODO: Adhere to MAX_CONNECTIONS
// TODO: Replace return statements, make sure to close any open FDs too
void command_processor_thread()
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

	xil_printf("CmdProc: Thread starting...\r\n");

	// Open server socket, stream mode
	if ((listenerSocket = lwip_socket(AF_INET, SOCK_STREAM, 0)) < 0)
	{
		xil_printf("CmdProc: Can't open socket, aborting...\r\n");
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
		xil_printf("CmdProc: Can't bind to socket %d, aborting...\r\n", CMD_PORT);
		return;
	}

	// Begin listening, register listener as FD of interest to read
	if (lwip_listen(listenerSocket, 5) < 0)
	{
		xil_printf("CmdProc: Can't listen on socket %d, aborting...\r\n", CMD_PORT);
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
					numBytesRead = better_read(i, pRxBuffer, sizeof(struct protocol_header), 0);

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
								numBytesRead = better_read(i, pRxBuffer+sizeof(struct protocol_header), pRxHeader->payload_sz, 0);
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
						command_dispatcher(pRxHeader, pTxHeader, pRxBuffer+sizeof(struct protocol_header), pTxBuffer+sizeof(struct protocol_header));

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
	xil_printf("CmdProc: Exiting thread! [SHOULD NEVER EXECUTE!]\r\n");

}



// New protocol command dispatcher
// Note: it is assumed that the packet is well formed before by it being passed to this function
// Also command processor thread means that command == CMD_ACCESS, the only currently supported command ;)
//
// TODO: Ensure read methods do not exceed MAX_PAYLOAD_SIZE
// TODO: Remove invalid operation clauses from switch bank
void command_dispatcher(struct protocol_header* pRxHeader,
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
			// TODO: Complete BUS_RDMA when we have spec of downstream config block
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
void test_thread()
{
	/*
	// *** For LM82 tests ***
	int localTemp = 0;
	int remoteTemp = 0;
	u8 cmd = LM82_REG_READ_STATUS;
	u8 stat = 0;
	*/

	// *** For EEPROM tests ***
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

	// *** For FEM config struct tests ***
	struct fem_config cfg;

	// Initalise LM82 device with setpoints we can easily trigger
	initLM82(29,32);		// (warn temp, crit temp)

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
		xil_printf("Test:  Local LM82 temp: %dc\r\n", localTemp);
		xil_printf("Test: Remote LM82 temp: %dc\r\n", remoteTemp);
		xil_printf("Test:  Status register: 0x%x\r\n", stat);
	}
	*/

	// ------------------------------------------------------------------------
	// EEPROM tester

	/*
	sleep(2000);

	// Blank out first 8 pages for testing
	for (i=0; i<8; i++)
	{
		writeToEEPROM((i*16), blankData, 16);
	}

	// Do test write
	writeToEEPROM(7, dummyData, 34);

	// Do readback to check data
	xil_printf("----------------------\r\n");
	readFromEEPROM(0, readBuffer, 8192);
	for (i=0; i<16; i++)
	{
		// sooo ugly :(
		if (i==0) { xil_printf("00"); }
		xil_printf("%x: %x %x %x %x %x %x %x %x   %x %x %x %x %x %x %x %x \r\n",
			(i*16)*16, readBuffer[(i*16)+0], readBuffer[(i*16)+1], readBuffer[(i*16)+2], readBuffer[(i*16)+3], readBuffer[(i*16)+4], readBuffer[(i*16)+5], readBuffer[(i*16)+6], readBuffer[(i*16)+7],
			readBuffer[(i*16)+8], readBuffer[(i*16)+9], readBuffer[(i*16)+10], readBuffer[(i*16)+11], readBuffer[(i*16)+12], readBuffer[(i*16)+13], readBuffer[(i*16)+14], readBuffer[(i*16)+15] );
	}
	*/

	// ------------------------------------------------------------------------
	// Rob RDMA / RS232 link test

	/*
	int n=0;
	u32 uartBaseAddr = XPAR_RS232_UART_2_BASEADDR;

	xil_printf("Test: Running RDMA readback test (using UART 0x%x @ %d)\r\n", uartBaseAddr, XPAR_RS232_UART_2_BAUDRATE);

	// Build test packets
	// Format is:  Command (1 byte)  |  Address (4 bytes LSB first)  |  Value (4 bytes LSB first)
	u8 rdmaReadCommand[] =		{
									RDMA_CMD_READ,
									0x1, 0x0, 0x0, 0x0
								};

	u8 rdmaWriteCommand[] =		{
									RDMA_CMD_WRITE,
									0x1, 0x0, 0x0, 0x0,
									0xDE, 0xAD, 0xBE, 0xEF
								};


	u8 rdmaReadbackCommand[] =	{
									RDMA_CMD_READ,
									0x4, 0x0, 0x0, 0x0
								};

	u8 rdmaInboundPacket[4];

	// No point tracking number of bytes sent with xuartlite_l as it doesn't tell us...

	// Read register
	for (n=0; n<sizeof(rdmaReadCommand); n++)
	{
		// Send read
		xil_printf("Test: Sending byte %d...\r\n", n);
		XUartLite_SendByte(uartBaseAddr, rdmaReadCommand[n]);
	}
	for (n=0; n<4; n++)
	{
		// Get response
		xil_printf("Test: Reading byte %d...\r\n", n);
		rdmaInboundPacket[n] = XUartLite_RecvByte(uartBaseAddr);
	}
	xil_printf("Test: Read RDMA register: 0x%x, 0x%x, 0x%x, 0x%x\r\n", rdmaInboundPacket[0], rdmaInboundPacket[1], rdmaInboundPacket[2], rdmaInboundPacket[3]);

	// -=-

	// Write register
	for (n=0; n<sizeof(rdmaWriteCommand); n++)
	{
		XUartLite_SendByte(uartBaseAddr, rdmaWriteCommand[n]);
	}
	xil_printf("Test: Wrote RDMA register.\r\n");

	// -=-

	// Readback register 0x0
	for (n=0; n<sizeof(rdmaReadbackCommand); n++)
	{
		// Send read
		XUartLite_SendByte(uartBaseAddr, rdmaReadbackCommand[n]);
	}
	xil_printf("Test: Wrote RDMA register.\r\n");
	for (n=0; n<4; n++)
	{
		// Get response
		rdmaInboundPacket[n] = XUartLite_RecvByte(uartBaseAddr);
	}
	xil_printf("Test: Readback RDMA register: 0x%x, 0x%x, 0x%x, 0x%x\r\n", rdmaInboundPacket[0], rdmaInboundPacket[1], rdmaInboundPacket[2], rdmaInboundPacket[3]);
	*/

	// New RS232_RDMA test
	xil_printf("Test: Running RDMA test v2...\r\n");
	u32 addr;
	u32 regVal = 0;

	// Read read-only register
	addr = 4;
	regVal = readRdma(RDMA_RS232_BASEADDR, addr);
	xil_printf("Test: RO:RDMA register 0x%x = 0x%x\r\n", addr, regVal);

	// Read read-write register
	addr = 1;
	regVal = readRdma(RDMA_RS232_BASEADDR, addr);
	xil_printf("Test: RW:RDMA register 0x%x = 0x%x\r\n", addr, regVal);

	// Write read-write register
	u32 testValue = 0xDEADBEEF;
	writeRdma(RDMA_RS232_BASEADDR, addr, testValue);
	xil_printf("Test: Wrote 0x%x to 0x%x\r\n", addr, testValue);

	// Read read-write register
	regVal = readRdma(RDMA_RS232_BASEADDR, addr);
	xil_printf("Test: RW:RDMA register 0x%x = 0x%x\r\n", addr, regVal);

	// Don't let EEPROM tests run!
	return;

	// ------------------------------------------------------------------------
	// FEM configuration struct test
	// TODO: Complete
	cfg.mac_address[0]       = 0x00;
	cfg.mac_address[1]       = 0x0A;
	cfg.mac_address[2]       = 0x35;
	cfg.mac_address[3]       = 0x00;
	cfg.mac_address[4]       = 0x01;
	cfg.mac_address[5]       = 0x02;
	cfg.temp_high_setpoint   = 29;
	cfg.temp_crit_setpoint   = 32;
	cfg.sw_major_version     = 1;
	cfg.sw_minor_version     = 0;
	cfg.fw_major_version     = 1;
	cfg.fw_minor_version     = 0;
	cfg.hw_major_version     = 1;
	cfg.hw_minor_version     = 0;
	cfg.board_id             = 0xA5;
	cfg.board_type           = 0xCE;

	xil_printf("Test: Thread exiting.\r\n");
}

// Reads the specified number of bytes from the given socket within the timeout period or returns an error code
int better_read(int sock, u8* pBuffer, unsigned int numBytes, unsigned int timeoutMs)
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
			DBGOUT("better_read: Hit maximum retries, bailing out...\r\n");
			return -1;
		}

	}

	//DBGOUT("better_read: Took %d loops to get %d bytes!\r\n", tempNumLoops, numBytes);
	return totalBytes;
}
