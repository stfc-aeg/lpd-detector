import time
from FemClient.FemClient import  *
from FemApi.FemTransaction import FemTransaction


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

flag_message = ["No", "Yes"]

# Fem has three internal i2c buses, power card uses bus 0x300
i2cInternalBusOffset = 0x300

# ad7998 device addresses
adc_chip_address = [0x22, 0x21, 0x24, 0x23]

class lpd_i2c_test(FemClient):
    
    #def __init__(self):
    def __init__(self, hostAddr=None, timeout=None):
        
        # Call superclass initialising function
        super(lpd_i2c_test, self).__init__(hostAddr, timeout)
        
        
    def read_dac(self):
        ''' Read ad5321 device 
        '''
        readLen = 2
        addr = i2cInternalBusOffset + 0x0C
        readback = -1
        
        readback = self.i2cRead(addr, readLen)
#        print "\nread_dac() readback = ", readback
        high = (readback[4] & 15) << 8
        low = readback[5]
#        Wire.requestFrom(0x0C, 2)
#        readback = ((Wire.receive() & 15) << 8)
#        readback |= Wire.receive()
#        return readback
        return high + low


    def read_adc(self, deviceId):
        ''' Read ad7998's adc values
        '''
        
        # bus, width parameters needed by the generic read/write functions;
        #     They are not necessary for the i2c specific read/write functions
        bus = 2
        width = 1
        addr = i2cInternalBusOffset + adc_chip_address[deviceId >> 3]
        txValue = 0x80 + ((deviceId & 7) << 4)

        # Debug info:
#        print "\t\t  ", bus, "\t", width, "\t", addr, "\t", txValue
        
        # Write
        ack = self.write(bus, width, addr, txValue)

        rxLen = 2
        # Read
        response = self.read(bus, width, addr, rxLen)
        
#        print ack, " : ", response
        
        # Extract the two bytes of data received
        high = (response[4] & 15) << 8
        low = response[5]
        return high + low
#            Wire.beginTransmission(chip)
#            Wire.send(0x80 + ((deviceId & 7) << 4))
#            Wire.endTransmission()
#            Wire.requestFrom(chip, 2)
#            result = ((Wire.receive() & 15) << 8)
#            result |= Wire.receive()
#            return result

    def read_bit(self, id):
        ''' Read one data from some kind of device? 
        '''
        value = -1
        addr = i2cInternalBusOffset + 0x38 
        
        response = self.i2cRead(addr, 1)
        value = response[4]
        #Wire.requestFrom(i2cInternalBusOffset, 1)
        #value = Wire.receive()
        return (value & (1 << id)) != 0
        

    def read_all_bits(self):
        ''' Read one byte from the device at address 0x38
        '''
        addr = i2cInternalBusOffset + 0x38
        response = self.i2cRead(addr, 1)
#        print "read_all_bits() response = ", response
        return response[4]

    def write_bit(self, id, value):
        
        bit_register = self.read_all_bits()
        bit_register = (bit_register & ~(1 << id)) | (value << id) | 0xFC

        addr = i2cInternalBusOffset + 0x38
        response = self.i2cWrite(addr, bit_register)
        
#        Wire.beginTransmission(0x38)
#        Wire.send(bit_register)
#        Wire.endTransmission()

    
    def  write_electrical_value(self, value, scale, unit):
        ''' Display argument value, formatted according to argument scale
        '''
        try:
            print " ",
            print round( float(value * scale / 4095.0), 2),
            print unit,
            print " [",
            print value,
            print "]",
        except Exception as errStr:
            print "write_electrical_value Exception: ", errStr
            

    def write_temperature_value(self, value, scale, unit):
        ''' Display argument value, formatted according to argument scale
        '''
        try:
            print " ",
            print round( float(value * scale / 4095.0), 2),
            print unit,
            print " [",
            print value,
            print "]",
        except Exception as errStr:
            print "write_temperature_value Exception: ", errStr

    def show_outputs(self):
        
        print "Outputs:"
        print "   V FEM      :",
        self.write_electrical_value(self.read_adc(V5_VOLTS_CHAN), 6, "V")
        self.write_electrical_value(self.read_adc(V5_AMPS_CHAN), 10, "A")
        print "."
        print "   V Digital  :",
        self.write_electrical_value(self.read_adc(V12_VOLTS_CHAN), 3, "V")
        self.write_electrical_value(self.read_adc(V12_AMPS_CHAN), 700, "mA")
        print "."
        print "."
        print "   V Sensor A :",
        self.write_electrical_value(self.read_adc(V25A_VOLTS_CHAN), 3, "V")
        self.write_electrical_value(self.read_adc(V25A_AMPS_CHAN), 10, "A")
        print "."
        print "   V Sensor B :",
        self.write_electrical_value(self.read_adc(V25B_VOLTS_CHAN), 3, "V")
        self.write_electrical_value(self.read_adc(V25B_AMPS_CHAN), 10, "A")
        print "."
        print "   V Sensor C :",
        self.write_electrical_value(self.read_adc(V25C_VOLTS_CHAN), 3, "V")
        self.write_electrical_value(self.read_adc(V25C_AMPS_CHAN), 10, "A")
        print "."
        print "   V Sensor D :",
        self.write_electrical_value(self.read_adc(V25D_VOLTS_CHAN), 3, "V")
        self.write_electrical_value(self.read_adc(V25D_AMPS_CHAN), 10, "A")
        print "."
        print "   V Sensor E :",
        self.write_electrical_value(self.read_adc(V25E_VOLTS_CHAN), 3, "V")
        self.write_electrical_value(self.read_adc(V25E_AMPS_CHAN), 10, "A")
        print "."
        print "   V Sensor F :",
        self.write_electrical_value(self.read_adc(V25F_VOLTS_CHAN), 3, "V")
        self.write_electrical_value(self.read_adc(V25F_AMPS_CHAN), 10, "A")
        print "."
        print "   V Sensor G :",
        self.write_electrical_value(self.read_adc(V25G_VOLTS_CHAN), 3, "V")
        self.write_electrical_value(self.read_adc(V25G_AMPS_CHAN), 10, "A")
        print "."
        print "   V Sensor H :",
        self.write_electrical_value(self.read_adc(V25H_VOLTS_CHAN), 3, "V")
        self.write_electrical_value(self.read_adc(V25H_AMPS_CHAN), 10, "A")
        print "."
        print "."
        print "   HV Bias  :",
        self.write_electrical_value(self.read_adc(HV_VOLTS_CHAN), 600, "V")
        self.write_electrical_value(self.read_adc(HV_AMPS_CHAN), 600, "uA")
        print "."
        print "."

    def show_lv_status(self):
        ''' Display the low voltage status
        '''        
        
        print "Status:"
        
        if (self.read_bit(LV_CTRL_BIT)):
            print "   Low  voltage is off." 
        else: 
            print "   Low  voltage is on." 
  


    def show_hv_status(self):
        ''' Display the higher voltage status
        '''
        value = -1
        if (self.read_bit(HV_CTRL_BIT)): 
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
        print flag_message[(value & (1 << FAULT_FLAG_BIT)) != 0],
        print ".\n",
        print "   Fem Status   Trip  = ",
        print flag_message[(value & (1 << FEM_STATUS_BIT)) != 0],
        print ".\n",
        print "   External     Trip  = ",
        print flag_message[(value & (1 << EXT_TRIP_BIT)) != 0],
        print ".\n",
        print "   Over current Trip  = ",
        print flag_message[(value & (1 << OVERCURRENT_BIT)) != 0],
        print ".\n",
        print "   Over temp    Trip  = ",
        print flag_message[(value & (1 << HIGH_TEMP_BIT)) != 0],
        print ".\n",
        print "   Undertemp          = ",
        print flag_message[(value & (1 << LOW_TEMP_BIT)) != 0],
        print ".\n",
        print ".\n",

    def show_temperatures(self):
        ''' Display the PSU card and sensor temperatures
        '''

        print "Temperature readings: "
        print "   Temp PSU card: ",
        self.write_temperature_value(self.read_adc(PSU_TEMP_CHAN),3, "V")
        print "."
        print "   Temp Sensor A: ",
        self.write_temperature_value(self.read_adc(SENSA_TEMP_CHAN),3, "V")
        print "."
        print "   Temp Sensor B: ",
        self.write_temperature_value(self.read_adc(SENSB_TEMP_CHAN),3, "V")
        print "."
        print "   Temp Sensor C: ",
        self.write_temperature_value(self.read_adc(SENSC_TEMP_CHAN),3, "V")
        print "."
        print "   Temp Sensor D: ",
        self.write_temperature_value(self.read_adc(SENSD_TEMP_CHAN),3, "V")
        print "."
        print "   Temp Sensor E: ",
        self.write_temperature_value(self.read_adc(SENSE_TEMP_CHAN),3, "V")
        print "."
        print "   Temp Sensor F: ",
        self.write_temperature_value(self.read_adc(SENSF_TEMP_CHAN),3, "V")
        print "."
        print "   Temp Sensor G: ",
        self.write_temperature_value(self.read_adc(SENSG_TEMP_CHAN),3, "V")
        print "."
        print "   Temp Sensor H: ",
        self.write_temperature_value(self.read_adc(SENSH_TEMP_CHAN),3, "V")
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
    
    # Define FEM IP address and port
    host = '192.168.2.2'
    port = 6969
    
    thisClass = lpd_i2c_test((host, port))

    # Test reading out the voltages on current first, then these ones:
    thisClass.displayAll()

    # Test switching the low voltage on..
    print "Switching low voltage on.."
    thisClass.write_bit(LV_CTRL_BIT, ON)
    print "Low voltage now on!"
    time.sleep(5)

    print "Let's check the status now:"
    thisClass.displayAll()
    
    print "Switching low voltage off.. "
    thisClass.write_bit(LV_CTRL_BIT, OFF)
    print "Low voltage now switched off!"

    # Close down the connection
    thisClass.close()
    
    
