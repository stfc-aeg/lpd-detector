'''

@author: ckd
'''

import time, types, sys
import argparse

from FemClient.FemClient import  *
from FemApi.FemTransaction import FemTransaction

class LpdI2cError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)

# -=-=-=~=~=~=-=-=- #
"""
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

"""


class LpdI2cTest(FemClient):

    # ADC channel numbers
    HV_VOLTS_CHAN =      0
    V5_VOLTS_CHAN =      1
    V12_VOLTS_CHAN =     2
    HV_AMPS_CHAN =       3
    V5_AMPS_CHAN =       4
    V12_AMPS_CHAN =      5
    PSU_TEMP_CHAN =      6
    V25A_VOLTS_CHAN =    8
    V25B_VOLTS_CHAN =    9
    V25C_VOLTS_CHAN =   10
    V25D_VOLTS_CHAN =   11
    V25E_VOLTS_CHAN =   12
    V25F_VOLTS_CHAN =   13
    V25G_VOLTS_CHAN =   14
    V25H_VOLTS_CHAN =   15
    V25A_AMPS_CHAN =    16
    V25B_AMPS_CHAN =    17
    V25C_AMPS_CHAN =    18
    V25D_AMPS_CHAN =    19
    V25E_AMPS_CHAN =    20
    V25F_AMPS_CHAN =    21
    V25G_AMPS_CHAN =    22
    V25H_AMPS_CHAN =    23
    SENSA_TEMP_CHAN =   24
    SENSB_TEMP_CHAN =   25
    SENSC_TEMP_CHAN =   26
    SENSD_TEMP_CHAN =   27
    SENSE_TEMP_CHAN =   28
    SENSF_TEMP_CHAN =   29
    SENSG_TEMP_CHAN =   30
    SENSH_TEMP_CHAN =   31

    # Bit numbers for control bits
    HV_CTRL_BIT    = 0
    LV_CTRL_BIT    = 1
    
    # Values for control bits
    OFF = 1
    ON  = 0
    
    # Bit numbers for status bits
    FEM_STATUS_BIT = 2
    EXT_TRIP_BIT   = 3
    FAULT_FLAG_BIT = 4
    OVERCURRENT_BIT =5
    HIGH_TEMP_BIT  = 6
    LOW_TEMP_BIT   = 7
    
    # Values for status bits
    TRIPPED = 1
    FAULT   = 1
    NORMAL  = 0
    
    # Enumarate fault flag as either cleared (0) or tripped (1) 
    flag_message = ["No", "Yes"]
    
    # ad7998 device addresses
    adc_chip_address = [0x22, 0x21, 0x24, 0x23]
    
    # Fem has three internal i2c buses, power card uses bus 0x300
    i2cInternalBusOffset = 0x300
    

    # Dictionary of hostname -> 1g IP address
    one1gAddress = {'te7burntoak'  : '192.168.2.2',
                    'te7kiribati'  : '192.168.3.2',
                    'devgpu02'     : '192.168.3.2',}

    def __init__(self, hostAddr=None, timeout=None):
        
        # Call superclass initialising function
        super(LpdI2cTest, self).__init__(hostAddr, timeout)

        
    def read_dac(self):
        ''' Read 2 bytes from ad5321 device 
        '''
        
        addr = LpdI2cTest.i2cInternalBusOffset + 0x0C
        response = -1
        
        response = self.i2cRead(addr, 2)
        high = (response[0] & 15) << 8
        low = response[1]
        return high + low


    def read_adc(self, deviceId):
        ''' Read 2 bytes from deviceId channel in ad7998
        
            Note: deviceId is a temp, current, etc, adc value at address deviceId.
                  i2c address is calculated from argument deviceId
                  ad7998 must receive the channel number (write operation)
                  before channel value can be read back (read operation)
        '''
        # Check input within valid range
        if (0 > deviceId) or (deviceId > 31):
            raise LpdI2cError("Read_adc() deviceId argument outside valid range (0 - 31)")
        
        addr = LpdI2cTest.i2cInternalBusOffset + LpdI2cTest.adc_chip_address[deviceId >> 3]
        adcChannel = 0x80 + ((deviceId & 7) << 4)

        # Write operation, select ADC channel
        ack = self.i2cWrite(addr, adcChannel)
        
        # Read operation, read ADC value
        response = self.i2cRead(addr, 2)
        
        #print " RAW response: ", response,
        
        # Extract the received two bytes and return as integer
        high = (response[0] & 15) << 8
        low = response[1]
        return high + low

    def read_bit(self, id):
        ''' Read one byte from PCF7485 device and determine if bit 'id' is set.
        
            Note: bit 1 = 0, 2 = 1,  3 = 2, 4 = 4, 
                      5 = 8, 6 = 16, 7 = 32 8 = 64
            Therefore, id must be one of the following: [0, 1, 2, 4, 8, 16, 32, 64]
        '''
        # Check input within valid range
        validInput = [0, 1, 2, 4, 8, 16, 32, 64]
        #if (0 > id) or (id > 31):
        if not id in validInput:
            raise LpdI2cError("Read_bit() id argument outside valid list [0, 1, 2, 4, 8, 16, 32, 64]")
        
        addr = LpdI2cTest.i2cInternalBusOffset + 0x38 
        
        response = self.i2cRead(addr, 1)
        value = response[0]
        return (value & (1 << id)) != 0
        

    def read_all_bits(self):
        ''' Read and return one byte from PCF7485 device
        '''
        addr = LpdI2cTest.i2cInternalBusOffset + 0x38
        response = self.i2cRead(addr, 1)
        
        return response[0]

    def write_bit(self, id, value):
        ''' Change bit 'id' to 'value' in PCF7485 device
        '''
        # Check input within valid range
        validInput = [0, 1, 2, 4, 8, 16, 32, 64]
        
        if not id in validInput:
            raise LpdI2cError("Write_bit() id argument outside valid list [0, 1, 2, 4, 8, 16, 32, 64]")
        if (0 > value or value > 1):
            raise LpdI2cError("Write_bit() value argument must be either 0 or 1")
        
        # Read PCF7485's current value
        bit_register = self.read_all_bits()
        # Change bit 'id' to 'value'
        bit_register = (bit_register & ~(1 << id)) | (value << id) | 0xFC
#        print "write_bit(), bit_register = %X" % bit_register, "    value =%d, id=%d" % (value, id)
        
        addr = LpdI2cTest.i2cInternalBusOffset + 0x38
        response = self.i2cWrite(addr, bit_register)
        
        #TODO: Check the acknowledgement? (response)

    
    def write_electrical_value(self, value, scale, unit):
        ''' Display argument value, formatted by scale, post fixing 'unit'
        '''
        # Check argument types
        if not type(value) is types.IntType:
            raise LpdI2cError("Write_electrical_value() value argument not integer type")
        if not type(scale) is types.IntType:
            raise LpdI2cError("Write_electrical_value() scale argument not integer type")
        if not type(unit) is types.StringType:
            raise LpdI2cError("Write_electrical_value() unit argument not string type")

        try:
            print " ",
            print round( float(value * scale / 4095.0), 2),
            print unit,
            print " [",
            print value,
            print "]",
        except Exception as e:
            print "write_electrical_value Exception: ", e
            

    def write_temperature_value(self, value, scale, unit):
        ''' Display argument value, formatted according to argument scale
        '''
        # Check argument types
        if not type(value) is types.IntType:
            raise LpdI2cError("Write_temperature_value() value argument not integer type")
        if not type(scale) is types.IntType:
            raise LpdI2cError("Write_temperature_value() scale argument not integer type")
        if not type(unit) is types.StringType:
            raise LpdI2cError("Write_temperature_value() unit argument not string type")

        try:
            print " ",
            print round( float(value * scale / 4095.0), 2),
            print unit,
            print " [",
            print value,
            print "]",
        except Exception as e:
            print "write_temperature_value Exception: ", e

    def show_outputs(self):
        ''' Display the output voltages and currents (Fem, Digital, Sensor, Bias)
        '''
        
        print "Outputs:"
        print "   V FEM      :",
        self.write_electrical_value( self.read_adc( LpdI2cTest.V5_VOLTS_CHAN ), 6, "V")
        self.write_electrical_value( self.read_adc( LpdI2cTest.V5_AMPS_CHAN ), 10, "A")
        print "."
        print "   V Digital  :",
        self.write_electrical_value( self.read_adc( LpdI2cTest.V12_VOLTS_CHAN ), 3, "V")
        self.write_electrical_value( self.read_adc( LpdI2cTest.V12_AMPS_CHAN ), 700, "mA")
        print "."
        print "."
        print "   V Sensor A :",
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25A_VOLTS_CHAN ), 3, "V")
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25A_AMPS_CHAN ), 10, "A")
        print "."
        print "   V Sensor B :",
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25B_VOLTS_CHAN ), 3, "V")
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25B_AMPS_CHAN ), 10, "A")
        print "."
        print "   V Sensor C :",
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25C_VOLTS_CHAN ), 3, "V")
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25C_AMPS_CHAN ), 10, "A")
        print "."
        print "   V Sensor D :",
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25D_VOLTS_CHAN ), 3, "V")
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25D_AMPS_CHAN ), 10, "A")
        print "."
        print "   V Sensor E :",
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25E_VOLTS_CHAN ), 3, "V")
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25E_AMPS_CHAN ), 10, "A")
        print "."
        print "   V Sensor F :",
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25F_VOLTS_CHAN ), 3, "V")
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25F_AMPS_CHAN ), 10, "A")
        print "."
        print "   V Sensor G :",
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25G_VOLTS_CHAN ), 3, "V")
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25G_AMPS_CHAN ), 10, "A")
        print "."
        print "   V Sensor H :",
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25H_VOLTS_CHAN ), 3, "V")
        self.write_electrical_value( self.read_adc( LpdI2cTest.V25H_AMPS_CHAN ), 10, "A")
        print "."
        print "."
        print "   HV Bias  :",
        self.write_electrical_value( self.read_adc( LpdI2cTest.HV_VOLTS_CHAN ), 600, "V")
        self.write_electrical_value( self.read_adc( LpdI2cTest.HV_AMPS_CHAN ), 600, "uA")
        print "."
        print "."

    def show_lv_status(self):
        ''' Display the low voltage status
        '''        
        
        print "Status:"
        if (self.read_bit(LpdI2cTest.LV_CTRL_BIT)):
            print "   Low  voltage is off." 
        else: 
            print "   Low  voltage is on." 


    def show_hv_status(self):
        ''' Display the high voltage status
        '''

        if (self.read_bit(LpdI2cTest.HV_CTRL_BIT)): 
            print "   High voltage is off." 
        else: 
            print "   High voltage is on." 
        
        value = self.read_dac()
        print "   HV setting: ", 
        print value,
        print " [",
        print round( float( value * 500 / 4095.0), 2),
        print "V]." 


    def show_flags(self):
        ''' Display  the fault flags
        '''
        
        print "Flags:" 
        value = self.read_all_bits()
        print "   Fault flag         = ",
        print LpdI2cTest.flag_message[ (value & (1 << LpdI2cTest.FAULT_FLAG_BIT)) != 0],
        print ".\n",
        print "   Fem Status   Trip  = ",
        print LpdI2cTest.flag_message[ (value & (1 << LpdI2cTest.FEM_STATUS_BIT)) != 0],
        print ".\n",
        print "   External     Trip  = ",
        print LpdI2cTest.flag_message[ (value & (1 << LpdI2cTest.EXT_TRIP_BIT)) != 0],
        print ".\n",
        print "   Over current Trip  = ",
        print LpdI2cTest.flag_message[ (value & (1 << LpdI2cTest.OVERCURRENT_BIT)) != 0],
        print ".\n",
        print "   Over temp    Trip  = ",
        print LpdI2cTest.flag_message[ (value & (1 << LpdI2cTest.HIGH_TEMP_BIT)) != 0],
        print ".\n",
        print "   Undertemp          = ",
        print LpdI2cTest.flag_message[ (value & (1 << LpdI2cTest.LOW_TEMP_BIT)) != 0],
        print ".\n",
        print ".\n",

    def show_temperatures(self):
        ''' Display the PSU card and sensor temperatures
        '''

        print "Temperature readings: "
        print "   Temp PSU card: ",
        self.write_temperature_value( self.read_adc( LpdI2cTest.PSU_TEMP_CHAN ),3, "V")
        print "."
        print "   Temp Sensor A: ",
        self.write_temperature_value( self.read_adc( LpdI2cTest.SENSA_TEMP_CHAN ),3, "V")
        print "."
        print "   Temp Sensor B: ",
        self.write_temperature_value( self.read_adc( LpdI2cTest.SENSB_TEMP_CHAN ),3, "V")
        print "."
        print "   Temp Sensor C: ",
        self.write_temperature_value( self.read_adc( LpdI2cTest.SENSC_TEMP_CHAN ),3, "V")
        print "."
        print "   Temp Sensor D: ",
        self.write_temperature_value( self.read_adc( LpdI2cTest.SENSD_TEMP_CHAN ),3, "V")
        print "."
        print "   Temp Sensor E: ",
        self.write_temperature_value( self.read_adc( LpdI2cTest.SENSE_TEMP_CHAN ),3, "V")
        print "."
        print "   Temp Sensor F: ",
        self.write_temperature_value( self.read_adc( LpdI2cTest.SENSF_TEMP_CHAN ),3, "V")
        print "."
        print "   Temp Sensor G: ",
        self.write_temperature_value( self.read_adc( LpdI2cTest.SENSG_TEMP_CHAN ),3, "V")
        print "."
        print "   Temp Sensor H: ",
        self.write_temperature_value( self.read_adc( LpdI2cTest.SENSH_TEMP_CHAN ),3, "V")
        print "."
        print "."


    def displayAll(self):
        ''' Display low voltage, high-voltage, fault flags, temperatures and sensor data
        '''
        self.show_lv_status()
        self.show_hv_status()
        self.show_flags()
        self.show_temperatures()
        self.show_outputs()

# -=-=-=~=~=~=-=-=- #


    
if __name__ == "__main__":
    
                        
    # Create parser object and arguments
    parser = argparse.ArgumentParser(description="To switch on the LV, the syntax is: 'python LpdI2ctest.py --lv 1' ",
                                     epilog="Note: If the script is executed without any given flag,  the corresponding supply will be switched OFF. Sadly, this is a limitation inherit to Python's parse module.")
    
    parser.add_argument("--lv", help="switch LV on (1) or off (0)", type=int, choices=[0, 1])
    parser.add_argument("--hv", help="switch HV on (1) or off (0)", type=int, choices=[0, 1])
    args = parser.parse_args()

    
    # Define FEM IP address and port
#    host = '192.168.2.2' # Burntoak
#    host = '192.168.3.2' # Kiribati, devgpu02
    # Determine name of current machine
    fullDomainName = socket.gethostname()
    # Only need hostname, not domain part
    hostName = fullDomainName.partition('.')[0]
    # Locate corresponding IP address
    host = LpdI2cTest.one1gAddress[hostName]
#    print "Debug info: machine = '%s', IP = '%s'." % (hostName, host)    

    port = 6969

    print "lv, hv: ", args.lv, args.hv
    # Only use if they decided to switch off lv but switch on hv
    if (args.lv == 0) and(args.hv):
        print "You decided to switch on HV but switch off LV; Aborting.."
        sys.exit()
        
    print "Switching LV ",
    if args.lv:
        print "on, ",
    else:
        print "off, ",
    print " and HV ",
    if args.hv:
        print "on..\n"
    else:
        print "off..\n"

    
    print "~+~+~+~+~+~+~+~+~+~+~+~+~ Connecting to host: %s, port: %i ~+~+~+~+~+~+~+~+~+~+~+~+~" % (host, port)
    time.sleep(1)
    
    thisFem = LpdI2cTest((host, port))

    # Execute according to supplied flags
    if args.lv:
        print "Switching low voltage on.."
        thisFem.write_bit(LpdI2cTest.LV_CTRL_BIT, LpdI2cTest.ON)
        time.sleep(1)
        
        # Is HV set to be switched on?
        if args.hv:
            # Yes - switch HV on
            print "Switching high voltage on.."
            thisFem.write_bit(LpdI2cTest.HV_CTRL_BIT, LpdI2cTest.ON)
        else:
            # No - switch HV off
            print "Switching high voltage off.. "
            thisFem.write_bit(LpdI2cTest.HV_CTRL_BIT, LpdI2cTest.OFF)

        time.sleep(1)
    else:
        # Switch off lv
        
        # Switch off HV first
        
        print "Switching high voltage off.. "
        thisFem.write_bit(LpdI2cTest.HV_CTRL_BIT, LpdI2cTest.OFF)
        time.sleep(1)
        
        print "Switching low voltage off.. "
        thisFem.write_bit(LpdI2cTest.LV_CTRL_BIT, LpdI2cTest.OFF)
        time.sleep(1)


    # Test reading out the voltages on current first, then these ones:
    thisFem.displayAll()


    print "\nClosing down Fem connection.."
    # Close down the connection
    thisFem.close()
    
