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
 * Developed against Xilinx ML507 development board under EDK 13.1 (Linux)
 *
 * Tested and deployed to FEM v1 board successfully
 *
 * ----------------------------------------------------------------------------
 *
 * Version 1.4 - not for distribution
 *
 * ----------------------------------------------------------------------------
 *
 * CHANGELOG:
 *
 * 1.1		06-July-2011
 * 	- First functional implementation of FEM communications protocol
 *  - Bug fixes in network select / command processing
 *
 * 1.2		25-July-2011
 *  - RDMA protocol handling implemented
 *  - EEPROM store / retrieve config implemented
 *
 * 1.3		04-Aug-2011
 *  - Refactoring / tidying
 *  - Replaced all xil_printf for DBGOUT macro
 *
 * 1.4		24-Aug-2011
 *  - Reimplemented I2C code to be able to address multiple busses
 *  - Fixed number of operations in response packet as first u32
 *  - Made comms code adhere to MAX_PAYLOAD_SIZE for response packets
 *  - Created hooks for commandProcessorThread to drop connections when already at connection limit,
 *  	but this isn't yet fully implemented...
 *
 * ----------------------------------------------------------------------------
 *
 * TO DO LIST:
 *
 * TODO: Determine why execution halts sometimes after LWIP auto-negotiation
 *
 * TODO: Clean network select / command processing logic, make robust
 * TODO: Test with malformed packets, try to break processing loop
 *
 * TODO: Support for concurrent large payload writes (????)
 *
 * TODO: Implement iperf server and some way to activate / deactivate it without rebooting or rebuilding
 *
 * TODO: Profile memory usage
 * TODO: Tune thread stacksize
 * TODO: Check for memory leaks
 * TODO: Determine why LWIP hangs on init using priority based scheduler
 *
 * ----------------------------------------------------------------------------
 */



// ----------------------------------------------------------------------------
// Includes
// ----------------------------------------------------------------------------

// Make sure xmk is included first, always!  [XilKernel]
#include "xmk.h"

// FEM includes
#include "fem.h"
#include "femConfig.h"

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

// ML507 specific hardware
#ifdef HW_PLATFORM_DEVBOARD
#include "gpio.h"
#include "xgpio.h"
#endif

// Testing and benchmarking
#include "test.h"
#include "iperf.h"

// EDK hardware includes
#include "xintc.h"
#include "xtmrctr.h"

// Calibrated sleep for MicroBlaze
#include "calib_sleep.h"

// Protocol command processor
#include "commandProcessor.h"



// ----------------------------------------------------------------------------
// Function Prototypes
// ----------------------------------------------------------------------------

void* masterThread(void *);			// Main thread launched by xilkernel
void networkInitThread(void *);	// Sets up LWIP, spawned by master thread
void initHardware(void);



// ----------------------------------------------------------------------------
// Global Variable Definitions
// ----------------------------------------------------------------------------

// TODO: Tidy up global variables!
struct netif		server_netif;
struct fem_config	femConfig;
XIntc				intc;
XTmrCtr				timer;

// Define our GPIOs if we are using ML507
#ifdef HW_PLATFORM_DEVBOARD
XGpio gpioLed8, gpioLed5, gpioDip, gpioSwitches;
#endif



// ----------------------------------------------------------------------------
// Functions
// ----------------------------------------------------------------------------

int main()
{
    init_platform();
    initHardware();
    xilkernel_init();
    xmk_add_static_thread(masterThread, 0);			// Create the master thread
    xilkernel_start();
    cleanup_platform();								// Never reached

    return 0;
}



// Master thread
void* masterThread(void *arg)
{

	sys_thread_t t;

	// Why doesn't LWIP initialise if we use SCHED_PRIO?  Is it because we haven't set a thread priority yet?

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
    t = sys_thread_new("netman", networkInitThread, NULL, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);
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
void networkInitThread(void *p)
{

	sys_thread_t t;

    struct netif *netif;
    struct ip_addr ipaddr, netmask, gateway;

    netif = &server_netif;

    // Setup network
    IP4_ADDR(&ipaddr,  femConfig.net_ip[0], femConfig.net_ip[1], femConfig.net_ip[2], femConfig.net_ip[3]);
    IP4_ADDR(&netmask, femConfig.net_nm[0], femConfig.net_nm[1], femConfig.net_nm[2], femConfig.net_nm[3]);
    IP4_ADDR(&gateway, femConfig.net_gw[0], femConfig.net_gw[1], femConfig.net_gw[2], femConfig.net_gw[3]);
    DBGOUT("NetMan: Activating network interface...\r\n");

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
    //t = sys_thread_new("test", testThread, 0, THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);

    if (t==NULL)
    {
    	DBGOUT("NetMan: Can't spawn thread, aborting...\r\n");
    }

    //DBGOUT("NetMan: Thread exiting\r\n");
}



/*
 * Initialises FEM hardware
 *
 */
void initHardware(void)
{

	int status;

	DBGOUT("\r\n\r\n----------------------------------------------------------------------\r\n");

#ifdef HW_PLATFORM_DEVBOARD
	DBGOUT("InitHardware: Platform is defined as XILINX DEVELOPMENT BOARD\r\n");
#else
	DBGOUT("InitHardware: Platform is defined as FEM HARDWARE\r\n");
#endif

	DBGOUT("InitHardware: System alive!  Starting initialisation...\r\n");

#ifdef HW_PLATFORM_DEVBOARD
    // Initialise GPIO devices (only for ML507)
    if (initGpioDevices(&gpioLed8, &gpioLed5, &gpioDip, &gpioSwitches) == -1)
    {
    	DBGOUT("InitHardware: Failed to initialise GPIOs.\r\n");
    }
#endif

    // Initialise timer
    // Timer will give results in CPU ticks, so use XPAR_CPU_PPC440_CORE_CLOCK_FREQ_HZ in calculations!
    status = XTmrCtr_Initialize(&timer, XPAR_XPS_TIMER_0_DEVICE_ID);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("InitHardware: Failed to initialise timer.\r\n");
    }

    // Calibrate usleep
    // On PPC usleep is implemented using the CPU time base register but on
    // MicroBlaze we need to do this ourselves using the timer.
    status = calibrateSleep(&timer);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("InitHardware: Failed to calibrate sleep.\r\n");
    }

    // Initialise and configure interrupt controller
    status = XIntc_Initialize(&intc, XINTC_ID);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("InitHardware: Failed to initialise interrupt controller.\r\n");
    }
    status = XIntc_Start(&intc, XIN_REAL_MODE);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("InitHardware: Failed to start interrupt controller.\r\n");
    }

    // Get config structure from EEPROM or use failsafe
    if (readConfigFromEEPROM(0, &femConfig) == -1)
    {
    	DBGOUT("InitHardware: Can't get configuration from EEPROM, using failsafe defaults...\r\n");
    	createFailsafeConfig(&femConfig);
    }
    else
    {
    	DBGOUT("InitHardware: Got configuration from EEPROM OK!\r\n");
    }

    // Show IP address
    DBGOUT("InitHardware: Network IP: %3d.%3d.%3d.%3d\r\n", femConfig.net_ip[0],femConfig.net_ip[1],femConfig.net_ip[2],femConfig.net_ip[3]);
    DBGOUT("InitHardware: Network NM: %3d.%3d.%3d.%3d\r\n", femConfig.net_nm[0],femConfig.net_nm[1],femConfig.net_nm[2],femConfig.net_nm[3]);
    DBGOUT("InitHardware: Network GW: %3d.%3d.%3d.%3d\r\n", femConfig.net_gw[0],femConfig.net_gw[1],femConfig.net_gw[2],femConfig.net_gw[3]);

    // Show LM82 setpoints
    DBGOUT("InitHardware: LM82 high temp @ %dc\r\n", femConfig.temp_high_setpoint);
    DBGOUT("InitHardware: LM82 crit temp @ %dc\r\n", femConfig.temp_crit_setpoint);

}

