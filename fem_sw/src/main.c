/**
 * ----------------------------------------------------------------------------
 * @brief	FEM Embedded Acquisition Platform - Power PC #2 - C&C interface
 *
 * @author	Matt Thorpe (matt.thorpe@stfc.ac.uk), Application Engineering Department, STFC RAL
 *
 * @details	Provides FEM command and control interface over TCP/IP socket using
 * 			Hard TEMAC and 1GBe interface.  Supports read / write operations on all
 * 			hardware busses and inter-PPC mailbox communications.
 * 			Functionality expandable by using FEM Personality Modules (FPM).
 * ----------------------------------------------------------------------------
 *
 * TO DO LIST: (in order of descending importance)
 *
 * HARDWARE:
 * TODO: Determine why execution halts sometimes after LWIP auto-negotiation - xlltemacif_hw.c -> Line 78?
 *
 * FUNCTIONALITY:
 * TODO: Move freeing large packet payload buffer and reallocing nominal size one to new method? (used both in disconnectClient and in STATE_HDR_VALID state...)
 * TODO: Implement FPM packet processing in commandHandler to prevent duplicated code
 * TODO: Re-enable BADPKT response sending where necessary (generateBadPacketResponse())
 * TODO: Clean up RDMA wrapper (was kludged into place and never fixed!)
 * TODO: Implement iperf server and some way to activate / deactivate it without rebooting or rebuilding
 *
 * GENERAL:
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

// Memory test
#include "xil_testmem.h"

// SystemACE
#ifndef HW_PLATFORM_DEVBOARD
#include "sysace.h"
#endif

// GPIO
#include "xgpio.h"
#ifdef HW_PLATFORM_DEVBOARD
#include "gpio.h"
#endif

// Testing and benchmarking
#include "test.h"
#include "iperf.h"

// EDK hardware includes
#include "xintc.h"
#include "xtmrctr.h"
//#include "xexception_l.h"
#include "xil_exception.h"

// Xilinx mailbox
#ifndef HW_PLATFORM_DEVBOARD
#include "mailbox.h"
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
struct netif		server_netif;
struct fem_config	femConfig;
XIntc				intc;
XTmrCtr				timer;

// Board specific objects
#ifdef HW_PLATFORM_DEVBOARD
// Define our GPIOs if we are using ML507
XGpio gpioLed8, gpioLed5, gpioDip, gpioSwitches;
#else
XSysAce				sysace;
XGpio 				gpioMux;
#endif

u32 femErrorState;

// ----------------------------------------------------------------------------
// Functions
// ----------------------------------------------------------------------------

int main()
{
	// Platform initialisation
    init_platform();

	// Flush serial console
	int clr;
	for (clr=0; clr<100; clr++)
	{
		DBGOUT("\r\n");
	}

	// Initialise hardware
    initHardware();

    // Initialise xilkernel
    xilkernel_init();

    // Create the master thread
    xmk_add_static_thread(masterThread, 0);

    // Start kilkernel
    xilkernel_start();

    // Never reached!
    cleanup_platform();
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

    // Launch application thread (pass GPIO instance for RDMA MUX setting)
    t = sys_thread_new("cmd", commandProcessorThread, &gpioMux, NET_THREAD_STACKSIZE, DEFAULT_THREAD_PRIO);

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
 * @return XST_SUCCESS if all hardware initialised OK, or XST_FAILURE if there were any errors
 *
 */
int initHardware(void)
{

	int status = 0;
	int fpgaTemp,lmTemp = 0;

	// Clear FEM error state
	femErrorState = 0;

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

    // Show memory and cache information
    DBGOUT("initHardware: DDR2: 0x%08x - 0x%08x ", FEM_DDR2_START, FEM_DDR2_START+FEM_DDR2_SIZE);
#ifdef USE_CACHE
    DBGOUT(" cache ENABLED\r\n");
#else
    DBGOUT(" cache DISABLED\r\n");
#endif

    // ****************************************************************************
    // Initialise timer
    // Timer will give results in CPU ticks, so use XPAR_CPU_PPC440_CORE_CLOCK_FREQ_HZ in calculations!
    status = XTmrCtr_Initialize(&timer, TIMER_ID);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to initialise timer.\r\n");
    	femErrorState |= TEST_TIMER_INIT;
    }
    // ****************************************************************************

    // ****************************************************************************
    // Calibrate usleep
    // On PPC usleep is implemented using the CPU time base register but on
    // MicroBlaze we need to do this ourselves using the timer.
    status = calibrateSleep(&timer);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to calibrate sleep.\r\n");
    	femErrorState |= TEST_TIMER_CALIB;
    }
    // ****************************************************************************

    // ****************************************************************************
    // Initialise and configure interrupt controller
    status = XIntc_Initialize(&intc, XINTC_ID);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to initialise interrupt controller.\r\n");
    	femErrorState |= TEST_INTC_INIT;
    }
    XIntc_SetOptions(&intc, XIN_SVC_ALL_ISRS_OPTION);
    // ****************************************************************************

    // This fails on anything other than the first boot as (I assume) buy then it's already started..?
    // Hardware reset fixes this.
    /*
    status = XIntc_SelfTest(&intc);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Interrupt controller failed self test!\r\n");
    	femErrorState |= TEST_INTC_BIST;
    }
    */

    // ****************************************************************************
    // Enable I2C interrupts
    //XIntc_Enable(&intc, I2C_INT_ID_EEPROM);
    XIntc_Enable(&intc, I2C_INT_ID_LM82);
    //XIntc_Enable(&intc, I2C_INT_ID_PWR_RHS);
    //XIntc_Enable(&intc, I2C_INT_ID_PWR_LHS);

    // Register callback for I2C interrupts
    /*
    status = XIntc_Connect(&intc, I2C_INT_ID_EEPROM, (XInterruptHandler)XIic_InterruptHandler, (void*)&iicEeprom);
    if (status != XST_SUCCESS)
	{
		DBGOUT("initHardware: Failed to connect I2C ISR (EEPROM).\r\n");
		femErrorState |= TEST_INTC_CON_EEPROM;
	}
    */

	status = XIntc_Connect(&intc, I2C_INT_ID_LM82, (XInterruptHandler)XIic_InterruptHandler, (void*)&iicLm82);
    if (status != XST_SUCCESS)
	{
		DBGOUT("initHardware: Failed to connect I2C ISR (LM82).\r\n");
		femErrorState |= TEST_INTC_CON_LM82;
	}

    /*
    status = XIntc_Connect(&intc, I2C_INT_ID_PWR_RHS, (XInterruptHandler)XIic_InterruptHandler, (void*)&iicRhs);
    if (status != XST_SUCCESS)
	{
		DBGOUT("initHardware: Failed to connect I2C ISR (POWER_RHS).\r\n");
		femErrorState |= TEST_INTC_CON_PWR_RHS;
	}

	status = XIntc_Connect(&intc, I2C_INT_ID_PWR_LHS, (XInterruptHandler)XIic_InterruptHandler, (void*)&iicLhs);
    if (status != XST_SUCCESS)
	{
		DBGOUT("initHardware: Failed to connect I2C ISR (POWER_LHS).\r\n");
		femErrorState |= TEST_INTC_CON_PWR_LHS;
	}
	*/
    // ****************************************************************************

    // ****************************************************************************
    // Start I2C controllers
    status = initI2C();
    if (status != XST_SUCCESS)
	{
		DBGOUT("initHardware: Failed to initialise I2C controllers.\r\n");
		femErrorState |= TEST_I2C_INIT;
	}
    // ****************************************************************************

    // ****************************************************************************
    // Start interrupt controller
    status = XIntc_Start(&intc, XIN_REAL_MODE);
    if (status != XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to initialise interrupt controller.\r\n");
    	femErrorState |= TEST_INTC_START;
    }
    // ****************************************************************************

    // ****************************************************************************
    // Enable interrupts (PPC)
    //XExc_mEnableExceptions(XEXC_ALL);
    Xil_ExceptionEnable();
    // ****************************************************************************

    // ****************************************************************************
    // Get config structure from EEPROM or use failsafe defaults
    if (readConfigFromEEPROM(0, &femConfig) == -1)
    {
    	DBGOUT("initHardware: Can't get configuration from EEPROM, using failsafe defaults...\r\n");
    	femErrorState |= TEST_I2C_EEPROM_CFG_READ;		// Not critical but should be reported
    	createFailsafeConfig(&femConfig);
    }
    // ****************************************************************************

    // ****************************************************************************
    // Show LM82 setpoints, and set them
    DBGOUT("initHardware: LM82 overheat limit %dc, shutdown limit %dc\r\n", femConfig.temp_high_setpoint, femConfig.temp_crit_setpoint);
    if(initLM82(femConfig.temp_high_setpoint, femConfig.temp_crit_setpoint)==-1)
    {
    	DBGOUT("initHardware: ERROR: Failed to initialise LM82.\r\n");
    	femErrorState |= TEST_I2C_LM82_INIT;
    }

    /*
    // Read FPGA temp
    fpgaTemp = readTemp(LM82_REG_READ_REMOTE_TEMP);
    lmTemp = readTemp(LM82_REG_READ_LOCAL_TEMP);
    if (fpgaTemp!=0 && lmTemp!=0)
    {
    	DBGOUT("initHardware: FPGA temp %dc, LM82 temp %dc\r\n", fpgaTemp, lmTemp);
    }
    else if (fpgaTemp==-1)
    {
    	DBGOUT("initHardware: ERROR - FPGA temperature read error!\r\n");
    	femErrorState |= TEST_I2C_LM82_EXT_T_READ;
    }
    else if (lmTemp==-1)
    {
    	DBGOUT("initHardware: ERROR - LM82 temperature read error!\r\n");
    	femErrorState |= TEST_I2C_LM82_INT_T_READ;
    }
    else
    {
    	DBGOUT("initHardware: WARNING - I2C accesses don't seem to be working, can't read system temperature!\r\n");
    	femErrorState |= TEST_I2C_LM82_EXT_T_READ;
    	femErrorState |= TEST_I2C_LM82_INT_T_READ;
    }
	*/
    // ****************************************************************************

    // ****************************************************************************
    // Initialise RDMA block(s) and run selftest
    status = initRdma();
    if (status!=XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to initialise RDMA controller.\r\n");
    	// TODO: FEM error state
    }
    status = rdmaSelftest();
    if (status == XST_UART_TEST_FAIL)
    {
    	DBGOUT("initHardware: RDMA UART loopback test failed.\r\n");
    	femErrorState |= TEST_RDMA_UART_BIST;
    }
    // ****************************************************************************

    // ****************************************************************************
    // Initialise SystemACE
    status = XSysAce_Initialize(&sysace, XSYSACE_ID);
    if (status!=XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to initialise SystemACE.\r\n");
    	femErrorState |= TEST_SYSACE_INIT;
    }

    // Self-test on SystemACE
    status = mySelfTest(&sysace);		// Returns XST_SUCCESS or XST_FAILURE
    if (status!=XST_SUCCESS)
    {
    	DBGOUT("initHardware: SystemACE failed self-test.\r\n");
    	DBGOUT("initHardware: Ignoring SystemACE failed self-test.\r\n");
    	femErrorState |= TEST_SYSACE_BIST;
    }
    else
    {
        // Test file write
        // TODO: Do CF test, set TEST_SYSACE_FILESYSTEM if fails
    }
    // ****************************************************************************

    // ****************************************************************************
    // Initialise mailbox
    status = initMailbox();
    if (status!=XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to initialise mailbox.\r\n");
    	femErrorState |= TEST_MBOX_INIT;
    }
    // ****************************************************************************

    // ****************************************************************************
    // Initialise GPIO mux controller
	#ifndef HW_PLATFORM_DEVBOARD
	status = XGpio_Initialize(&gpioMux, GPIO_ID);
	if (status!=XST_SUCCESS)
	{
		DBGOUT("initHardware: Failed to initialise GPIO mux.\r\n");
		femErrorState |= TEST_GPIO_MUX_INIT;
	}
	XGpio_SetDataDirection(&gpioMux, 1, 0x00);	// All outputs
	XGpio_DiscreteWrite(&gpioMux, 1, 0);		// Set to 0
    #endif
	// ****************************************************************************

	// ****************************************************************************
    // Call FEM personality module hardware init
    status = fpmInitHardware();
    if (status!=XST_SUCCESS)
    {
    	DBGOUT("initHardware: Failed to initialise FPM hardwares.\r\n");
    	femErrorState |= TEST_FPM_INIT;
    }
    // ****************************************************************************



    if (femErrorState==0) {
    	return XST_SUCCESS;
    }
    else
    {
    	DBGOUT("ERROR: Hardware initialisation failed - error code 0x%08x\r\n", femErrorState);
    	return XST_FAILURE;
    }

}
