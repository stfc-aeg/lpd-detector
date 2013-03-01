'''
Created on 25 Sep 2012

@author: tcn
'''

from collections import OrderedDict

# Parameter access types
AccessInit  = 0
AccessRead  = 1
AccessWrite = 2
    
# Parameter assignment policy - assignmentPolicy or mandatory
AssignmentOptional = True
AssignmentMandatory = False

class AttributeContainer(object):

    '''
    Simple class to provide structured container for parameter attributes. It is designed
    to simply enforce a consistent description of the required attributes a device
    parameter must possess, as defined by the Karabo parameter schema
    '''
        
    def __init__(self, paramType, displayedName, description, minValueOrRange, maxValue, defaultValue,
                   accessType, assignmentPolicy, unitName='', unitSymbol=''):
        
        # If the parameter type describes a vector, e.g. specified as [int], then set vector flag
        # and set the element type to that of the contained type. 
        # TODO: deal with composite types or reject them?
        if isinstance(paramType, (list, tuple)):
            self.type = paramType[0]
            self.numElements = len(paramType)
        else:
            self.type = paramType
            self.numElements = 1
            
        self.displayedName = displayedName
        self.description   = description
        
        # The parameter can be described in terms of a min and max value for a continuous range, or a
        # list of legal values, passed through the minValueOrRange parameter. Test if the minValueOrRange
        # is such a list and set attributes accordingly 
        if isinstance(minValueOrRange, (list, tuple)):
            self.possVals = tuple(minValueOrRange)
            self.minValue = None
            self.maxValue = None
        else:
            self.possVals = None
            self.minValue = minValueOrRange
            self.maxValue = maxValue
            
        self.defaultValue     = defaultValue
        self.accessType       = accessType
        self.assignmentPolicy = assignmentPolicy
        self.unitName         = unitName
        self.unitSymbol       = unitSymbol
        
        
class LpdDeviceParameters(object):
    '''
    LpdDeviceParameters
    
    This class defines the allowed parameters for the LPD device, making them accessible as a dictionary
    of key/value pairs, where the value is a set of required attributes each parameter possesses.
    '''


    def __init__(self):
        '''
        Constructor
        
        This constructor simply populates the object with a set of defined parameters for an LPD device,
        stored in the object as a key/value dictionary. The AttributeContainer class is used as the value
        to enforce the set of required attributes each parameter must possess. The set of parameters can be
        retrieved from the object using the get() method. 
        '''
        
        # parameters is a dictionary of allowed parameters, with a camelCase key and data in the form of
        # a tuple that specifies everything in Sergei's 'Karabo Parameter Templates' document, namely:
        #
        # 'key' : ( type, displayed name, description, minimum possible value (or tuple of allowed values),
        #           max possible value (ignored if minimum is a tuple of possibles), default value,
        #           access type, assignment policy (True if assignment optional, otherwise mandatory), 
        #           unit name, unit symbol )
    
        self.parameters = OrderedDict()

        #
        # Power card control parameters
        #
        
        self.parameters['sensorBias']           = AttributeContainer(float, 'SensorBias', 'Sensor HV Bias Voltage [V]',
                                                                        0, 500, 0,
                                                                        AccessWrite, True, 'volt', 'V' )
        
        self.parameters['sensorBiasEnable']     = AttributeContainer(bool, 'SensorBiasEnable', 'Sensor HV Bias Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional)
        
        self.parameters['asicPowerEnable']      = AttributeContainer(bool, 'AsicPowerEnable', 'ASIC LV Power Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional)
            
        #
        # Power card monitoring parameters
        #
        
        self.parameters['powerCardFault']       = AttributeContainer(bool, 'PowerCardFault', 'Power Card Fault Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, AssignmentOptional)
        
        self.parameters['powerCardFemStatus']   = AttributeContainer(bool, 'PowerCardFemStatus', 'Power Card FEM Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, AssignmentOptional)
        
        self.parameters['powerCardExtStatus']   = AttributeContainer(bool, 'PowerCardExtStatus', 'Power Card External Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, AssignmentOptional)
        
        self.parameters['powerCardOverCurrent'] = AttributeContainer(bool, 'PowerCardOverCurrent', 'Power Card Overcurrent Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, AssignmentOptional)
        
        self.parameters['powerCardOverTemp']    = AttributeContainer(bool, 'PowerCardOverTemp', 'Power Card Over Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, AssignmentOptional)
        
        self.parameters['powerCardUnderTemp']   = AttributeContainer(bool, 'PowerCardUnderTemp', 'Power Card Under Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None)
        
        self.parameters['powerCardTemp']        = AttributeContainer(float, 'PowerCardTemp', 'Power Card Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, 'Celsius', 'C')
        
        self.parameters['sensorATemp']          = AttributeContainer(float, 'SensorATemp', 'Sensor A Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, 'Celsius', 'C')
        
        self.parameters['sensorBTemp']          = AttributeContainer(float, 'SensorBTemp', 'Sensor B Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, 'Celsius', 'C')
                            
        self.parameters['sensorCTemp']          = AttributeContainer(float, 'SensorCTemp', 'Sensor C Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, 'Celsius', 'C')
        
        self.parameters['sensorDTemp']          = AttributeContainer(float, 'SensorDTemp', 'Sensor D Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, 'Celsius', 'C')
        
        self.parameters['sensorETemp']          = AttributeContainer(float, 'SensorETemp', 'Sensor E Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, 'Celsius', 'C')
        
        self.parameters['sensorFTemp']          = AttributeContainer(float, 'SensorFTemp', 'Sensor F Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C')
        
        self.parameters['sensorGTemp']          = AttributeContainer(float, 'SensorGTemp', 'Sensor G Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C')
        
        self.parameters['sensorHTemp']          = AttributeContainer(float, 'SensorHTemp', 'Sensor H Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C')
        
        self.parameters['femVoltage']           = AttributeContainer(float, 'FemVoltage', 'FEM 5V Supply Voltage [V]',
                                                                      0, 6,  None,
                                                                      AccessRead, None, 'Volts', 'V')
        
        self.parameters['femCurrent']           = AttributeContainer(float, 'FemCurrent', 'FEM 5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A')
        
        self.parameters['digitalVoltage']       = AttributeContainer(float, 'DigitalVoltage', 'ASIC 1.2V Digital Supply Voltage [V]',
                                                                      0, 2,  None,
                                                                      AccessRead, None, 'Volts', 'V')
        
        self.parameters['digitalCurrent']       = AttributeContainer(float, 'DigitalVoltage', 'ASIC 1.2V Digital Supply Current [mA]',
                                                                      0, 1000,  None,
                                                                      AccessRead, None, 'Milliamps', 'mA')
        
        self.parameters['sensorAVoltage']       = AttributeContainer(float, 'SensorAVoltage', 'Sensor A 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V')
        
        self.parameters['sensorACurrent']       = AttributeContainer(float, 'SensorACurrent', 'Sensor A 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A')
        
        self.parameters['sensorBVoltage']       = AttributeContainer(float, 'SensorBVoltage', 'Sensor B 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V')
        
        self.parameters['sensorBCurrent']       = AttributeContainer(float, 'SensorBCurrent', 'Sensor B 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A')
        
        self.parameters['sensorCVoltage']       = AttributeContainer(float, 'SensorCVoltage', 'Sensor C 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V')
        
        self.parameters['sensorCCurrent']       = AttributeContainer(float, 'SensorCCurrent', 'Sensor C 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A')
        
        self.parameters['sensorDVoltage']       = AttributeContainer(float, 'SensorDVoltage', 'Sensor D 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V')
        
        self.parameters['sensorDCurrent']       = AttributeContainer(float, 'SensorDCurrent', 'Sensor D 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A')
        
        self.parameters['sensorEVoltage']       = AttributeContainer(float, 'SensorEVoltage', 'Sensor E 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V')
        
        self.parameters['sensorECurrent']       = AttributeContainer(float, 'SensorECurrent', 'Sensor E 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A')
        
        self.parameters['sensorFVoltage']       = AttributeContainer(float, 'SensorFVoltage', 'Sensor F 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V')
        
        self.parameters['sensorFCurrent']       = AttributeContainer(float, 'SensorFCurrent', 'Sensor F 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A')
        
        self.parameters['sensorGVoltage']       = AttributeContainer(float, 'SensorGVoltage', 'Sensor G 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V')
        
        self.parameters['sensorGCurrent']       = AttributeContainer(float, 'SensorGCurrent', 'Sensor G 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A')
        
        self.parameters['sensorHVoltage']       = AttributeContainer(float, 'SensorHVoltage', 'Sensor H 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V')
        
        self.parameters['sensorHCurrent']       = AttributeContainer(float, 'SensorHCurrent', 'Sensor H 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A')
        
        self.parameters['sensorBiasVoltage']    = AttributeContainer(float, 'SensorBiasVoltage', 'Sensor bias voltage readback [V]',
                                                                      0, 600, None,
                                                                      AccessRead, None, 'Volts', 'V')
        
        self.parameters['sensorBiasCurrent']    = AttributeContainer(float, 'SensorBiasVoltage', 'Sensor bias current readback [uA]',
                                                                      0, 600, None,
                                                                      AccessRead, None, 'Microamps', 'uA')

        #
        # TenGig Ethernet UDP Parameters - two 10GiGE interfaces
        #
                            
        self.parameters['tenGig0SourceMac']     = AttributeContainer(str, 'TenGigE0SourceMAC', '10GigE 0 UDP Source MAC Address',
                                                                      None, None, '62-00-00-00-00-01',
                                                                      AccessWrite, AssignmentMandatory)
        
        self.parameters['tenGig0SourceIp']      = AttributeContainer(str, 'TenGigE0SourceIp', '10GigE 0 UDP Source IP Address',
                                                                      None, None, '10.0.1.1',
                                                                      AccessWrite, AssignmentMandatory)
        
        self.parameters['tenGig0SourcePort']    = AttributeContainer(int, 'TenGigE0SourcePort', '10GigE 0 UDP Source Port',
                                                                      0, 65535, 8,
                                                                      AccessWrite, AssignmentMandatory)
        
        self.parameters['tenGig0DestMac']       = AttributeContainer(str, 'TenGigE0DestMAC', '10GigE 0 UDP Destination MAC Address',
                                                                      None, None, '00-07-43-01-01-01',
                                                                      AccessWrite, AssignmentMandatory)
        
        self.parameters['tenGig0DestIp']        = AttributeContainer(str, 'TenGigE0DestIp', '10GigE 0 UDP Destination IP Address',
                                                                      None, None, '10.0.1.2',
                                                                      AccessWrite, AssignmentMandatory)
        
        self.parameters['tenGig0DestPort']      = AttributeContainer(int, 'TenGigE0DestPort', '10GigE 0 UDP Destination Port',
                                                                      0, 65535, 61649,
                                                                      AccessWrite, AssignmentMandatory)
        
        self.parameters['tenGig1SourceMac']     = AttributeContainer(str, 'TenGigE1SourceMAC', '10GigE 1 UDP Source MAC Address',
                                                                      None, None, '62-00-00-00-00-02',
                                                                      AccessWrite, AssignmentMandatory)
        
        self.parameters['tenGig1SourceIp']      = AttributeContainer(str, 'TenGigE1SourceIp', '10GigE 1 UDP Source IP Address',
                                                                      None, None, '10.0.2.1',
                                                                      AccessWrite, AssignmentMandatory)
        
        self.parameters['tenGig1SourcePort']    = AttributeContainer(int, 'TenGigE1SourcePort', '10GigE 1 UDP Source Port',
                                                                      0, 65535, 8,
                                                                      AccessWrite, AssignmentMandatory)
        
        self.parameters['tenGig1DestMac']       = AttributeContainer(str, 'TenGigE1DestMAC', '10GigE 1 UDP Destination MAC Address',
                                                                      None, None, '00-07-43-01-01-02',
                                                                      AccessWrite, AssignmentMandatory)
       
        self.parameters['tenGig1DestIp']        = AttributeContainer(str, 'TenGigE1DestIp', '10GigE 1 UDP Destination IP Address',
                                                                      None, None, '10.0.2.2',
                                                                      AccessWrite, AssignmentMandatory)
        
        self.parameters['tenGig1DestPort']      = AttributeContainer(int, 'TenGigE1DestPort', '10GigE 1 UDP Destination Port',
                                                                      0, 65535, 61649,
                                                                      AccessWrite, AssignmentMandatory)
        
        self.parameters['tenGigInterframeGap']  = AttributeContainer(int, 'TenGigInterframeGap', '10GigE Inter-frame gap timer [clock cycles]',
                                                                      0, 0xFFFFFFFF, 0x0,
                                                                      AccessWrite, AssignmentOptional)
        
        self.parameters['tenGigUdpPacketLen']   = AttributeContainer(int, 'TenGigUDPPacketLength', '10GigE UDP packet payload length',
                                                                      0, 65535, 8000,
                                                                      AccessWrite, AssignmentOptional)
                           
        #
        # LPD FEM firmware block parameters. Note these are simply based on all exposed
        # parameters in the original test scripts - many may be replaced or hard-coded in
        # production firmware iterations
        #
        
        #TODO: Redundant because there is no action if set to False?
        self.parameters['femFastCtrlDynamic']           = AttributeContainer(bool, 'FemFastCtrlDynamic', 'Enables fast control with dynamic vetos',
                                                                      (True, False), None, True,
                                                                      AccessWrite, AssignmentOptional)
        
        self.parameters['femEnableTenGig']              = AttributeContainer(bool, 'FemEnableTenGig', 'Enables transmission of image data via 10GigE UDP interface',
                                                                      (True, False), None, True,
                                                                      AccessWrite, AssignmentOptional)
        
        self.parameters['femDataSource']                = AttributeContainer(int, 'FemDataSource', 'Source of data sent to 10GigE: 0=ASIC (via PPC), 1=ASIC (from Rxblock), 2=frame generator, 3=PPC (preprogrammed)',
                                                                      0, 3, 1,
                                                                      AccessWrite, AssignmentOptional)
        
        self.parameters['femAsicModuleType']            = AttributeContainer(int, 'FemAsicModuleType', 'Selects type of ASIC module  0=supermodule, 1=single ASIC, 2=2-tile module, 3=stand-alone',
                                                                        0, 3, 2,
                                                                        AccessWrite, AssignmentOptional)
                
        self.parameters['femAsicEnableMask']            = AttributeContainer([int]*4, 'FemAsicEnableMask', 'ASIC RX channel enable mask (4*32 bits)',
                                                                         0, 0xFFFFFFFF, [0xFFFFFFFF]*4,
                                                                         AccessWrite, AssignmentMandatory)
        
        self.parameters['femAsicColumns']               = AttributeContainer(int, 'FemAsicColumns', 'Sets ASIC RX readout size (time-slices) per trigger',
                                                                         0, 255, 1,
                                                                         AccessWrite, AssignmentOptional)
        
        self.parameters['femAsicGainOverride']          = AttributeContainer(int, 'FemAsicGainOverride', 'Overrides ASIC gain selection algorithm (0=normal, 8=x100, 9=x10, 11=x1',
                                                                         (0, 8, 9, 11), None, 0,
                                                                         AccessWrite, AssignmentOptional)
        
        self.parameters['femAsicSlowControlParams']     = AttributeContainer(str, 'FemAsicSlowControlParams', 'ASIC slow control parameter definition in XML syntax',
                                                                            None, None, None,
                                                                            AccessWrite, AssignmentMandatory)
        
        self.parameters['femAsicFastCmdSequence']       = AttributeContainer(str, 'FemAsicFastCmdSequence', 'ASIC fast command (readout) sequence definition in XML syntax',
                                                                          None, None, None,
                                                                          AccessWrite, AssignmentMandatory)
        
        self.parameters['femAsicPixelFeedbackOverride'] = AttributeContainer(int, 'FemAsicPixelFeedbackOverride', 'ASIC per-pixel override of feedback selection: 0 = high(10p), 1= low(50p)',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentOptional)
        
        self.parameters['femAsicPixelSelfTestOverride'] = AttributeContainer(int, 'FemAsicPixelSelfTestOverride', 'ASIC per-pixel override of self-test enable: 1 = enabled',
                                                                          0, 1, 1,
                                                                          AccessWrite, AssignmentOptional)
        
        self.parameters['femReadoutOperatingMode']      = AttributeContainer(int, 'FemReadoutOperatingMode', 'FEM readout operating mode (e.g. normal, self-test scan etc, TBD',
                                                                          0, 255, 0,
                                                                          AccessWrite, AssignmentOptional)

        ############ Additional Variables ############
    
        self.parameters['femAsicDataType']      = AttributeContainer(int, 'FemAsicDataType', 'ASIC data type 0=sensor data, 1=rx counting, 2=pseudorandom',
                                                                          0, 2, 0,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femAsicLocalClock']    = AttributeContainer(int, 'FemAsicLocalClock', 'ASIC clock scaling 0=100 MHz, 1=scaled down clock (10 MHz)',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femFastCtrlDynamic']   = AttributeContainer(bool, 'FemFastCtrlDynamic', 'New dynamic ASIC commands',
                                                                          (True, False), None, True,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femAsicSlowLoadMode']  = AttributeContainer(int, 'FemAsicSlowLoadMode', 'ASIC control load mode 0=parallel, 1=serial',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femAsicRxInvertData']  = AttributeContainer(bool, 'FemAsicRxInvertData', 'Invert ADC ASIC data',
                                                                          (True, False), None, False,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femAsicRxFastStrobe']  = AttributeContainer(bool, 'FemAsicRxFastStrobe', 'Start ASIC capture using strobe derived from ASIC Command file',
                                                                          (True, False), None, True,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femAsicRxDelayOddChannels'] = AttributeContainer(bool, 'FemAsicRxDelayOddChannels', 'Delay odd ASIC data channels by one clock to fix alignment',
                                                                          (True, False), None, True,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femAsicSlowClockPhase']= AttributeContainer(int, 'FemAsicSlowClockPhase', 'ASIC additional phase adjustment of slow clock rsync wrt ASIC reset',
                                                                          0, 65535, 0,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femAsicSlowedClock']   = AttributeContainer(bool, 'FemAsicSlowedClock', 'ASIC readout phase is slowed down',
                                                                          (True, False), None, False,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femPpcMode']           = AttributeContainer(int, 'FemPpcMode', 'Fem PPC mode 0=single train shot with PPC reset, 1=Continuous readout',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femPpcResetDelay']     = AttributeContainer(int, 'FemPpcResetDelay', 'Delay after resetting ppc ',
                                                                          0, 10, 5,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femNumTestCycles']     = AttributeContainer(int, 'FemNumTestCycles', 'Number of test cycles if LL Data Generator or PPC Data Direct selected',
                                                                          0, 255, 1,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['tenGigFarmMode']       = AttributeContainer(int, 'TenGigFarmMode', '10GigE farm mode 1=disabled, 2=fixed IP,multi port, 3=farm mode with nic lists',
                                                                          1, 3, 1,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femI2cBus']            = AttributeContainer(int, 'FemI2cBus', 'Set Fem i2c internal bus 0x000=LM82, 0x100=EEPROM, 0x200=RHS Power Card, 0x300=LHS Power Card (2Tile System)',
                                                                          (0x000,  0x100, 0x200, 0x300), None, 0x300,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femAsicVersion']      = AttributeContainer(int, 'FemAsicVersion', 'ASIC version 1=version 1, 2=version 2',
                                                                          1, 2, 1,
                                                                          AccessWrite, AssignmentMandatory)

        self.parameters['femAsicClockSource']    = AttributeContainer(int, 'FemAsicClockSource', 'ASIC clock source 0=Fem local oscillator, 1=XFEL C&C System',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentMandatory)



    def get(self):
        '''
        Returns the dictionary of parameters built by the constructor
        '''
        return self.parameters
    
    def parameterTemplateStr(self, schemaName):
        '''
        Generator for building (incomplete) Karabo schema definitions for device parameters. This 
        is a crude text analogue of Sergei's example parameters. It would be better to replace
        AttributeContainer with the appropriate classes and use the schema to define parameters
        directly.
        '''
        
        # Mapping of native parameter type to Karabo parameter template expression
        paramTypeMapping = { 'int'    : 'UINT32_ELEMENT',
                             'long'   : 'UINT64_ELEMENT',
                             'bool'   : 'BOOL_ELEMENT',
                             'float'  : 'DOUBLE_ELEMENT',
                             'str'    : 'STRING_ELEMENT',
                           }
        
        # Mapping of access types to Karabo parameter template expression
        accessTypeMapping = { AccessInit : 'init()',
                              AccessRead : 'readOnly()',
                              AccessWrite : 'reconfigurable()'
                            }
        
        # Iterate over parameter dictionary, build a template string and yield it
        for param, attrib in self.parameters.iteritems():
    
            paramType = attrib.type.__name__

            # Prefix element definition with vector if required
            if attrib.numElements > 1:
                elementPrefix = 'VECTOR_'
            else:
                elementPrefix = ''
                
            templateStr = 'e = %s%s(%s)\n' % (elementPrefix, paramTypeMapping[paramType], schemaName)
            templateStr += 'e.key(\"%s\").displayedName(\"%s\")\n' % (param, attrib.displayedName)
            templateStr += 'e.description(\"%s\")\n' % (attrib.description)
            
            templateStr += 'e'
            # If parameter has optional assignment, insert call for it
            if attrib.assignmentPolicy == AssignmentOptional:
                templateStr += '.assignmentOptional()'
                # If parameter has a default value, insert it
                if attrib.defaultValue != None:
                    templateStr += '.defaultValue(' + repr(attrib.defaultValue) + ')'
                else:
                    templateStr += '.noDefaultValue()'
            elif attrib.assignmentPolicy == AssignmentMandatory:
                templateStr += '.assignmentMandatory()'
                
            # Insert access policy call
            templateStr += '.%s\n' % accessTypeMapping[attrib.accessType]
            
            # TODO - this is an incomplete implementation, which needs input from Sergei to complete! For instance,
            # mechanism for expression unit symbol and name was not present in the examples.     
                
            templateStr += 'e.commit()\n' 
            
            yield templateStr

            
# Main entry point allows this module to be called stand-alone and to generate a Karabo schema style
# list of LPD device parameters
 
if __name__ == '__main__':
    
    deviceParams = LpdDeviceParameters()
    for paramTemplate in deviceParams.parameterTemplateStr('expected'):
        print paramTemplate
