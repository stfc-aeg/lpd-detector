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
 * Provides Lightweight IP stack on xilkernel platform, supporting basic
 * remote register read / write functionality and full support for I2C
 * devices (M24C08 8k EEPROM, LM82 monitoring chip) using a simple socket interface.
 *
 * Provides support for FPM (FEM Personality Modules), providing application specific
 * functionality through special commands.
 *
 * Developed against Xilinx ML507 development board under EDK 13.1 (Linux)
 *
 * Ported to FEM production hardware
 *
 * ----------------------------------------------------------------------------
 *
 * Version 1.7 - not for distribution
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
 *
 * 1.5		23-Sep-2011
 *  - Revised RDMA library to support 16550 UART
 *  - Implemented RDMA self-test routine
 *
 * 1.6		03-Oct-2011
 *  - Added stub for internal state queries / CMD_INTERNAL
 *  - Added preliminary support for SystemACE / writing to CF via xilfatfs library
 *
 * 1.7		16-Nov-2011
 *  - Restructured network receive loop
 *  - Added support for large payloads (pixel memory configs, sysace images)
 *  - Introduced FEM personality modules
 *  - Added CMD_PERSONALITY for application-specific commands (passed to FEM personality module)
 *
 * ----------------------------------------------------------------------------
 *
 * TO DO LIST: (in order of descending importance)
 *
 * HARDWARE:
 * TODO: Determine why execution halts sometimes after LWIP auto-negotiation - xlltemacif_hw.c -> Line 78?
 * TODO: Determine why UART loopback test occasionally fails - Update 2012, have not seen this error in a looong time?
 * TODO: Determine xsysace failure modes - currently failing with status = 0x200.  Also get this error if no CF inserted so maybe card format is damaged? (On Saeed's V2 FEM w/CF I see 0x80?)
 *
 * FUNCTIONALITY:
 * TODO: Move freeing large packet payload buffer and reallocing nominal size one to new method? (used both in disconnectClient and in STATE_HDR_VALID state...)
 * TODO: Implement FPM packet processing in commandHandler to prevent duplicated code
 * TODO: How to let personality module run validateHeaderContents equivalent?
 * TODO: Re-enable BADPKT response sending where necessary (generateBadPacketResponse())
 * TODO: Provide access to femErrorState via CMD_INTERNAL
 * TODO: Clean up RDMA wrapper (was kludged into place and never fixed!)
 * TODO: Implement iperf server and some way to activate / deactivate it without rebooting or rebuilding
 *
 * GENERAL:
 * TODO: Profile memory usage
 * TODO: Tune thread stacksize
 * TODO: Check for memory leaks
 * TODO: Determine why LWIP hangs on init using priority based scheduler
 *
 * CODING STANDARDS:
 * TODO: Make const-correct! (urgh)
 * TODO: Replace pass-by-pointer to pass-by-reference where possible
 * TODO: Make method names consistent across all files
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

// SystemACE
#ifndef HW_PLATFORM_DEVBOARD
#include "sysace.h"
#endif

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

// Xilinx mailbox
#ifndef HW_PLATFORM_DEVBOARD
#include "xmbox.h"
#endif

// Calibrated sleep for MicroBlaze
#include "calib_sleep.h"

// Protocol command processor
#include "commandProcessor.h"

// FEM Personality module template
#include "personality.h"



// ----------------------------------------------------------------------------
// Function Prototypes
// ----------------------------------------------------------------------------

void* masterThread(void *);			// Main thread launched by xilkernel
void networkInitThread(void *);	// Sets up LWIP, spawned by master thread
int initHardware(void);

// ----------------------------------------------------------------------------
// Global Variable Definitions
// ----------------------------------------------------------------------------

// TODO: Tidy up global variables!
struct netif		server_netif;
struct fem_config	femConfig;
XIntc				intc;
XTmrCtr				timer;

// Board specific objects
#ifdef HW_PLATFORM_DEVBOARD
// Define our GPIOs if we are using ML507
XGpio gpioLed8, gpioLed5, gpioDip, gpioSwitches;
#else
// Enable SystemACE controller if using FEM (was not present in original ML507 BSP)
XSysAce				sysace;
// Enable IPC Mailbox
XMbox				mbox;
#endif


u32 femErrorState;

// ----------------------------------------------------------------------------
// Functions
// ----------------------------------------------------------------------------

int main()
{
    init_platform();
    //usleep(1000000);		// 1 second delay - TEMAC has still hung using this delay :(

    //DBGOUT("main: init_platform() complete.\r\n");
    initHardware();
    //DBGOUT("main: initHardware() complete.\r\n");
    xilkernel_init();
    //DBGOUT("main: xilkernel_init() complete.\r\n");
    xmk_add_static_thread(masterThread, 0);			// Create the master thread
    //DBGOUT("main: xmk_add_static complete.\r\n");
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
    DBGOUT("XilMaster: Initialising LWIP... ");
    lwip_init();
    DBGOUT("OK.\r\n");

    // Spawn LWIP manager thread
    DBGOUT("XilMaster: Spawning network manager thread\r\n");
    t = sys_thread_new("netman", networkInitThread, NULL, NET_THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);
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
    DBGOUT("NetMan: Device IP is %03d.%03d.%03d.%03d\r\n", femConfig.net_ip[0], femConfig.net_ip[1], femConfig.net_ip[2], femConfig.net_ip[3]);
    if (!xemac_add(netif, &ipaddr, &netmask, &gateway, (unsigned char*)femConfig.net_mac, BADDR_MAC)) {
    	DBGOUT("NetMan: Error adding N/W interface to netif, aborting...\r\n");
        return;
    }
    netif_set_default(netif);

    // Specify that the network if is up
    netif_set_up(netif);

    // Start packet receive thread - required for lwIP operation
    t = sys_thread_new("xemacif_input_thread", (void(*)(void*))xemacif_input_thread, netif, NET_THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);
    if (t==NULL)
    {
    	DBGOUT("NetMan: Can't spawn xemacif thread, aborting...\r\n");
    	return;
    }

    // Launch application thread
    t = sys_thread_new("cmd", commandProcessorThread, 0, NET_THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);

    // - OR -

    // Launch iperf thread
    //t = sys_thread_new("iperf", iperf_rx_application_thread, 0, NET_THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);

    // - OR -

    // Launch testing thread
    //t = sys_thread_new("test", testThread, 0, NET_THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);

    if (t==NULL)
    {
    	DBGOUT("NetMan: Can't spawn thread, aborting...\r\n");
    }

    //DBGOUT("NetMan: Thread exiting\r\n");
}



/*
 * Initialises FEM hardware
 *
 * @return XST_SUCCESS if all hardware initialised OK, otherwise error code
 *
 */
int initHardware(void)
{

	int status = 0;
	int fpgaTemp,lmTemp = 0;
	femErrorState = 0;

	// Clear serial console by spamming CR/LF
	int foo;
	for (foo=0; foo<100; foo++)
	{
		DBGOUT("\r\n");
	}

	DBGOUT("\r\n\r\n----------------------------------------------------------------------\r\n");
	DBGOUT("initHardware: System alive!\r\n");

#ifdef HW_PLATFORM_DEVBOARD
	DBGOUT("initHardware: Platform is defined as XILINX DEVELOPMENT BOARD\r\n");
#else
	DBGOUT("initHardware: Platform is defined as FEM HARDWARE\r\n");
#endif

#ifdef HW_PLATFORM_DEVBOARD
    // Initialise GPIO devices (only for ML507)
    if (initGpioDevices(&gpioLed8, &gpioLed5, &gpioDip, &gpioSwitches) == -1)
    {
    	DBGOUT("initHardware: Failed to initialise GPIOs.\r\n");
    }
#endif

    // Initialise timer
    // Timer will give results in CPU ticks, so use XPAR_CPU_PPC440_CORE_CLOCK_FREQ_HZ in calculations!
    status = XTmrCtr_Initialize(&timer, XPAR_XPS_TIMER_0_DEVICE_ID);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to initialise timer.\r\n");
    	femErrorState |= TEST_XPSTIMER_INIT;
    }

    // Calibrate usleep
    // On PPC usleep is implemented using the CPU time base register but on
    // MicroBlaze we need to do this ourselves using the timer.
    status = calibrateSleep(&timer);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to calibrate sleep.\r\n");
    	femErrorState |= TEST_TIMER_CALIB;
    }

    // Initialise and configure interrupt controller
    status = XIntc_Initialize(&intc, XINTC_ID);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to initialise interrupt controller.\r\n");
    	femErrorState |= TEST_XINTC_INIT;
    }
    status = XIntc_Start(&intc, XIN_REAL_MODE);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to start interrupt controller.\r\n");
    	femErrorState |= TEST_XINTC_START;
    }

    // Get config structure from EEPROM or use failsafe
    if (readConfigFromEEPROM(0, &femConfig) == -1)
    {
    	DBGOUT("initHardware: Can't get configuration from EEPROM, using failsafe defaults...\r\n");
    	femErrorState |= TEST_EEPROM_CFG_READ;		// Not really an error but client might like to know...
    	createFailsafeConfig(&femConfig);
    }
    else
    {
    	DBGOUT("initHardware: Got EEPROM configuration OK.\r\n");
    }

    // Show LM82 setpoints, and set them
    DBGOUT("initHardware: LM82 overheat limit %dc, shutdown limit %dc\r\n", femConfig.temp_high_setpoint, femConfig.temp_crit_setpoint);
    initLM82(femConfig.temp_high_setpoint, femConfig.temp_crit_setpoint);

    // Read FPGA temp
    fpgaTemp = readTemp(LM82_REG_READ_REMOTE_TEMP);
    lmTemp = readTemp(LM82_REG_READ_LOCAL_TEMP);
    if (fpgaTemp!=0 && lmTemp!=0)
    {
    	DBGOUT("initHardware: FPGA temp %dc, LM82 temp %dc\r\n", fpgaTemp, lmTemp);
    }
    else
    {
    	DBGOUT("initHardware: WARNING - I2C accesses don't seem to be working, can't read system temperature!\r\n");
    	// TODO: Set error?
    }

    // Initialise RDMA block(s) and run selftest
    initRdma();
    DBGOUT("initHardware: Running RDMA self-test... ");
    status = rdmaSelftest();
    if (status == XST_UART_TEST_FAIL)
    {
    	DBGOUT("FAILED - UART loopback test failed.\r\n");
    	femErrorState |= TEST_RDMA_UART_OK;
    	return status;
    }
    else if (status == XST_LOOPBACK_ERROR)
    {
    	DBGOUT("FAILED - RDMA readback test failed.\r\n");
    	femErrorState |= TEST_RDMA_READBACK;
    	return status;
    }
    else
    {
    	DBGOUT("OK.\r\n");
    }

    // SystemACE disabled until I know how the SA/SP3N/V5 interact....
    /*
     * Things I need to know:
     * 		How can I instruct the management spartan to allow the V5 to aquire MPU lock to SystemACE?
     *
     */

    // Initialise SystemACE
    status = XSysAce_Initialize(&sysace, XSYSACE_ID);
    if (status!=XST_SUCCESS)
    {
    	DBGOUT("initHardware: SystemACE failed initialisation.\r\n");
    	femErrorState |= TEST_SYSACE_INIT;
    	//return status;
    }
    else
    {
    	DBGOUT("initHardware: SystemACE initialised.\r\n");
    }

    // Self-test on SystemACE
    status = mySelfTest(&sysace);		// Returns XST_SUCCESS or XST_FAILURE
    if (status!=XST_SUCCESS)
    {
    	DBGOUT("initHardware: SystemACE failed self-test.\r\n");
    	DBGOUT("initHardware: Ignoring SystemACE failed self-test...\r\n");
    	femErrorState |= TEST_SYSACE_BIST;
    	//return status;
    }
    else
    {
        // Test file write
        //testCF();
    }

    // Call FEM personality module hardware init
    status = fpmInitHardware();
    if (status!=XST_SUCCESS)
    {
    	DBGOUT("initHardware: Personality module hardware initialisation failed...\r\n");
    }
    else
    {
    	DBGOUT("initHardware: Personality module hardware initialisation OK!\r\n");
    }

    // PPC1 communications tests - comment if not using PPC1 or PPC2 will hang on blocking read!
    // -----------------------------------------------------------------------------------------
    // TODO: Tidy / move
    /*
     *
#ifndef HW_PLATFORM_DEVBOARD
    // Generate Config
    XMbox_Config mboxCfg;
    mboxCfg.BaseAddress =	BADDR_MBOX;
    mboxCfg.DeviceId =		MBOX_ID;
    mboxCfg.RecvID =		MBOX_RECV_ID;
    mboxCfg.SendID =		MBOX_SEND_ID;
    mboxCfg.UseFSL =		MBOX_USE_FSL;
#endif

    status = XMbox_CfgInitialize(&mbox, &mboxCfg, BADDR_MBOX);
    if (status!=XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to configure mailbox...\r\n");
    }

    u32 ipcMessage = 0x22BEEF44;
    u32 reply = 0;
    u32 mboxSentBytes = 0;

    u32 sharedBramTest = 0xA52354BB;
    u32 *pBram = (u32*)XPAR_BRAM_0_BASEADDR;
    *pBram = sharedBramTest;

    status = XMbox_Write(&mbox, &ipcMessage, 4, &mboxSentBytes);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to sent mailbox msg to PPC1 :(\r\n");
    }
    else
    {
    	DBGOUT("initHardware: Sent mailbox msg (%d bytes) to PPC1!\r\n", mboxSentBytes);

    	// Get a reply - WARNING, BLOCKING CALL!
    	XMbox_ReadBlocking(&mbox, &reply, 4);
    	//if (status!=XST_SUCCESS) {
    	//	DBGOUT("initHardware: Failed to get response from PPC1...\r\n");
    	//} else {
    		if (reply==0xBEEF6969) {
    			DBGOUT("initHardware: Response is GOOD, Matt are great!\r\n");
    		} else {
    			DBGOUT("initHardware: Got response from PPC1 but it's incorrect :(\r\n");
    		}
    	//}

    }
    */
    // -----------------------------------------------------------------------------------------

    // All is well
    // TODO: Remove XST_SUCCESS, replace with status!
    return XST_SUCCESS;

}
