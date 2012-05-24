/*
 * gpio.c
 *
 * Initialisation function for ML505/507 GPIO devices
 *
 */

#include "gpio.h"

#ifdef HW_PLATFORM_DEVBOARD

/**
 * Initialises GPIO devices on devboard
 * @param pLed8 pointer to GPIO object connected to 8 LED bank
 * @param pLed5 pointer to GPIO object connected to 5 direction LEDs
 * @param pDip pointer to GPIO object connected to 8-way DIP switch bank
 * @param pSwitch pointer to GPIO object connected to 5 way direction buttons
 *
 * @return operation status
 */
int initGpioDevices(XGpio* pLed8, XGpio* pLed5, XGpio* pDip, XGpio* pSwitch)
{
	Xuint32 status;

	// 8x LED bank
	status = XGpio_Initialize(pLed8, XPAR_LEDS_8BIT_DEVICE_ID);
	if (status!=XST_SUCCESS)
	{
		return -1;
	}
	XGpio_SetDataDirection(pLed8, 1, 0x00);	// All chan 1 as outputs

	// Positions 5 LEDs
	status = XGpio_Initialize(pLed5, XPAR_LEDS_POSITIONS_DEVICE_ID);
	if (status!=XST_SUCCESS)
	{
		return -1;
	}
	XGpio_SetDataDirection(pLed5, 1, 0x00);	// All chan 1 as outputs

	// 8-way DIP switches
	status = XGpio_Initialize(pDip, XPAR_DIP_SWITCHES_8BIT_DEVICE_ID);
	if (status!=XST_SUCCESS)
	{
		return -1;
	}
	XGpio_SetDataDirection(pDip, 1, 0xFF);	// All chan 1 as inputs

	// Buttons
	status = XGpio_Initialize(pSwitch, XPAR_PUSH_BUTTONS_5BIT_DEVICE_ID);
	if (status!=XST_SUCCESS)
	{
		return -1;
	}
	XGpio_SetDataDirection(pSwitch, 1, 0xFF);	// All chan 1 as inputs

	// Turn LEDs off
	XGpio_DiscreteWrite(pLed8, 1, 0x00);
	XGpio_DiscreteWrite(pLed5, 1, 0x00);

	return 0;
}
#endif
