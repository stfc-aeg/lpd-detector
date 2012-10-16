'''
LpdFemClient - XFEL LPD class sitting between the API and the FemClient

             - Will be renamed LpdFemClient at some point in the future
            
Created 16 October 2012

@Author: ckd



  ADC channels:
    0 = HV volts    1 = 5V volts    2 = 1.2V volts
    3 = HV current  4 = 5V current  5 = 1.2V current
    6 = PSU temp    7 = not used
    8-15  = 2.5V volts (A-H)
    16-23 = 2.5V current (A-H)
    24-31 = Sensor temp (A-H)

  Bits:
    0 = [out] LV control (0=on)
    1 = [out] HV control (0=on)
    2 = unused
    3 = [in] External trip (1=tripped)
    4 = [in] Fault flag (1=tripped)
    5 = [in] Overcurrent (1=fault)
    6 = [in] High temperature (1=fault)
    7 = [in] Low temperature (1=fault)

'''

import sys

from FemClient.FemClient import *
from FemApi.FemTransaction import FemTransaction