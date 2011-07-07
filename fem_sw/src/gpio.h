/*
 * gpio.h
 *
 * Initialisation function for ML505/507 GPIO devices
 *
 */

#ifndef GPIO_H_
#define GPIO_H_

#include "xparameters.h"
#include "xgpio.h"

int initGpioDevices(XGpio* pLed8, XGpio* pLed5, XGpio* pDip, XGpio* pSwitch);

#endif /* GPIO_H_ */
