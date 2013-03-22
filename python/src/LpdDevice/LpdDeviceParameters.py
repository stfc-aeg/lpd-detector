'''
Created on 25 Sep 2012

@author: tcn
'''

from collections import OrderedDict

# Parameter access types
AccessInit  = 0
AccessRead  = 1
AccessWrite = 2
    
# Parameter assignment policy - optional or mandatory
AssignmentOptional = True
AssignmentMandatory = False

# Parameter internal flag - identifies parameters that are trapped at device level and not passed down
InternalParam = True
ExternalParam = False

class AttributeContainer(object):

    '''
    Simple class to provide structured container for parameter attributes. It is designed
    to simply enforce a consistent description of the required attributes a device
    parameter must possess, as defined by the Karabo parameter schema
    '''
        
    def __init__(self, paramType, displayedName, description, minValueOrRange, maxValue, defaultValue,
                   accessType, assignmentPolicy, isInternal, allowedStates, unitName='', unitSymbol=''):
        
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
        self.isInternal       = isInternal
        self.allowedStates    = allowedStates
        self.unitName         = unitName
        self.unitSymbol       = unitSymbol
        
        
class LpdDeviceParameters(object):
    '''
    LpdDeviceParameters
    
    This class defines the allowed expectedParameters for the LPD device, making them accessible as a dictionary
    of key/value pairs, where the value is a set of required attributes each parameter possesses.
    '''


    def __init__(self):
        '''
        Constructor
        
        This constructor simply populates the object with a set of defined internal and expected parameters for an LPD device,
        stored in the object as a key/value dictionary. The AttributeContainer class is used as the value
        to enforce the set of required attributes each parameter must possess. The set of parameters can be
        retrieved from the object using the getInternal() and getExpected() methods. 
        '''
        
        # expectedParameters is a dictionary of expected parameters, with a camelCase key and data in the form of
        # a tuple that specifies everything in Sergei's 'Karabo Parameter Templates' document, namely:
        #
        # 'key' : ( type, displayed name, description, minimum possible value (or tuple of allowed values),
        #           max possible value (ignored if minimum is a tuple of possibles), default value,
        #           access type, assignment policy (True if assignment optional, otherwise mandatory), 
        #           unit name, unit symbol )
    
        self.expectedParameters = OrderedDict()

        # Internal parameters used in the LpdDevice class but not passed down into the underlying client object
        
        self.expectedParameters['femHost']    = AttributeContainer(str, 'FEM Host', 'FEM hostname or IP address',
                                                                None, None, '127.0.0.1',
                                                                AccessWrite, AssignmentOptional, InternalParam, 
                                                                'AllOk.Disconnected')
        self.expectedParameters['femPort']    = AttributeContainer(int, 'FEM Port', 'FEM port number',
                                                                0, 65535, 6969,
                                                                AccessWrite, AssignmentOptional, InternalParam,
                                                                'AllOk.Disconnected')
        self.expectedParameters['femTimeout'] = AttributeContainer(int, 'FEM Timeout', 'FEM connection timeout',
                                                                0, 1000, 30,
                                                                AccessWrite, AssignmentOptional, InternalParam,
                                                                'AllOk.Disconnected')
        self.expectedParameters['femAsicModuleType'] = AttributeContainer(int, 'FemAsicModuleType', 
                                                                'Selects type of ASIC module  0=supermodule, 1=single ASIC, 2=2-tile module, 3=stand-alone',
                                                                0, 3, 0,
                                                                AccessWrite, AssignmentOptional, InternalParam, 
                                                                'AllOk.Disconnected')

        #
        # Power card control parameters
        #
        
        self.expectedParameters['sensorBias']           = AttributeContainer(float, 'SensorBias', 'Sensor HV Bias Voltage [V]',
                                                                        0, 500, 0,
                                                                        AccessWrite, True, ExternalParam, 
                                                                        'AllOk.Idle', 'volt', 'V' )
        
        self.expectedParameters['sensorBiasEnable']     = AttributeContainer(bool, 'SensorBiasEnable', 'Sensor HV Bias Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional, ExternalParam,
                                                                        'AllOk.Idle')
        
        self.expectedParameters['asicPowerEnable']      = AttributeContainer(bool, 'AsicPowerEnable', 'ASIC LV Power Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional, ExternalParam,
                                                                        'AllOk.Idle')
            
        #
        # Power card monitoring parameters
        #
        
        self.expectedParameters['powerCardFault']       = AttributeContainer(bool, 'PowerCardFault', 'Power Card Fault Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardFemStatus']   = AttributeContainer(bool, 'PowerCardFemStatus', 'Power Card FEM Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardExtStatus']   = AttributeContainer(bool, 'PowerCardExtStatus', 'Power Card External Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardOverCurrent'] = AttributeContainer(bool, 'PowerCardOverCurrent', 'Power Card Overcurrent Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardOverTemp']    = AttributeContainer(bool, 'PowerCardOverTemp', 'Power Card Over Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardUnderTemp']   = AttributeContainer(bool, 'PowerCardUnderTemp', 'Power Card Under Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardTemp']        = AttributeContainer(float, 'PowerCardTemp', 'Power Card Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensorATemp']          = AttributeContainer(float, 'SensorATemp', 'Sensor A Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensorBTemp']          = AttributeContainer(float, 'SensorBTemp', 'Sensor B Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
                            
        self.expectedParameters['sensorCTemp']          = AttributeContainer(float, 'SensorCTemp', 'Sensor C Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensorDTemp']          = AttributeContainer(float, 'SensorDTemp', 'Sensor D Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensorETemp']          = AttributeContainer(float, 'SensorETemp', 'Sensor E Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensorFTemp']          = AttributeContainer(float, 'SensorFTemp', 'Sensor F Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensorGTemp']          = AttributeContainer(float, 'SensorGTemp', 'Sensor G Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensorHTemp']          = AttributeContainer(float, 'SensorHTemp', 'Sensor H Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['femVoltage']           = AttributeContainer(float, 'FemVoltage', 'FEM 5V Supply Voltage [V]',
                                                                      0, 6,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['femCurrent']           = AttributeContainer(float, 'FemCurrent', 'FEM 5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['digitalVoltage']       = AttributeContainer(float, 'DigitalVoltage', 'ASIC 1.2V Digital Supply Voltage [V]',
                                                                      0, 2,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['digitalCurrent']       = AttributeContainer(float, 'DigitalVoltage', 'ASIC 1.2V Digital Supply Current [mA]',
                                                                      0, 1000,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Milliamps', 'mA')
        
        self.expectedParameters['sensorAVoltage']       = AttributeContainer(float, 'SensorAVoltage', 'Sensor A 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensorACurrent']       = AttributeContainer(float, 'SensorACurrent', 'Sensor A 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensorBVoltage']       = AttributeContainer(float, 'SensorBVoltage', 'Sensor B 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensorBCurrent']       = AttributeContainer(float, 'SensorBCurrent', 'Sensor B 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensorCVoltage']       = AttributeContainer(float, 'SensorCVoltage', 'Sensor C 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensorCCurrent']       = AttributeContainer(float, 'SensorCCurrent', 'Sensor C 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensorDVoltage']       = AttributeContainer(float, 'SensorDVoltage', 'Sensor D 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensorDCurrent']       = AttributeContainer(float, 'SensorDCurrent', 'Sensor D 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensorEVoltage']       = AttributeContainer(float, 'SensorEVoltage', 'Sensor E 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensorECurrent']       = AttributeContainer(float, 'SensorECurrent', 'Sensor E 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensorFVoltage']       = AttributeContainer(float, 'SensorFVoltage', 'Sensor F 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensorFCurrent']       = AttributeContainer(float, 'SensorFCurrent', 'Sensor F 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensorGVoltage']       = AttributeContainer(float, 'SensorGVoltage', 'Sensor G 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensorGCurrent']       = AttributeContainer(float, 'SensorGCurrent', 'Sensor G 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensorHVoltage']       = AttributeContainer(float, 'SensorHVoltage', 'Sensor H 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensorHCurrent']       = AttributeContainer(float, 'SensorHCurrent', 'Sensor H 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensorBiasVoltage']    = AttributeContainer(float, 'SensorBiasVoltage', 'Sensor bias voltage readback [V]',
                                                                      0, 600, None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensorBiasCurrent']    = AttributeContainer(float, 'SensorBiasVoltage', 'Sensor bias current readback [uA]',
                                                                      0, 600, None,
                                                                      AccessRead, None, ExternalParam, None, 'Microamps', 'uA')

        #
        # TenGig Ethernet UDP Parameters - two 10GiGE interfaces
        #
                            
        self.expectedParameters['tenGig0SourceMac']     = AttributeContainer(str, 'TenGigE0SourceMAC', '10GigE 0 UDP Source MAC Address',
                                                                      None, None, '62-00-00-00-00-01',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGig0SourceIp']      = AttributeContainer(str, 'TenGigE0SourceIp', '10GigE 0 UDP Source IP Address',
                                                                      None, None, '10.0.1.1',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGig0SourcePort']    = AttributeContainer(int, 'TenGigE0SourcePort', '10GigE 0 UDP Source Port',
                                                                      0, 65535, 8,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGig0DestMac']       = AttributeContainer(str, 'TenGigE0DestMAC', '10GigE 0 UDP Destination MAC Address',
                                                                      None, None, '00-07-43-01-01-01',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGig0DestIp']        = AttributeContainer(str, 'TenGigE0DestIp', '10GigE 0 UDP Destination IP Address',
                                                                      None, None, '10.0.1.2',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGig0DestPort']      = AttributeContainer(int, 'TenGigE0DestPort', '10GigE 0 UDP Destination Port',
                                                                      0, 65535, 61649,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGig1SourceMac']     = AttributeContainer(str, 'TenGigE1SourceMAC', '10GigE 1 UDP Source MAC Address',
                                                                      None, None, '62-00-00-00-00-02',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGig1SourceIp']      = AttributeContainer(str, 'TenGigE1SourceIp', '10GigE 1 UDP Source IP Address',
                                                                      None, None, '10.0.2.1',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGig1SourcePort']    = AttributeContainer(int, 'TenGigE1SourcePort', '10GigE 1 UDP Source Port',
                                                                      0, 65535, 8,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGig1DestMac']       = AttributeContainer(str, 'TenGigE1DestMAC', '10GigE 1 UDP Destination MAC Address',
                                                                      None, None, '00-07-43-01-01-02',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
       
        self.expectedParameters['tenGig1DestIp']        = AttributeContainer(str, 'TenGigE1DestIp', '10GigE 1 UDP Destination IP Address',
                                                                      None, None, '10.0.2.2',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGig1DestPort']      = AttributeContainer(int, 'TenGigE1DestPort', '10GigE 1 UDP Destination Port',
                                                                      0, 65535, 61649,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGigInterframeGap']  = AttributeContainer(int, 'TenGigInterframeGap', '10GigE Inter-frame gap timer [clock cycles]',
                                                                      0, 0xFFFFFFFF, 0x0,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['tenGigUdpPacketLen']   = AttributeContainer(int, 'TenGigUDPPacketLength', '10GigE UDP packet payload length',
                                                                      0, 65535, 8000,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
                           
        #
        # LPD FEM firmware block parameters. Note these are simply based on all exposed
        # parameters in the original test scripts - many may be replaced or hard-coded in
        # production firmware iterations
        #
        
        #TODO: Redundant because there is no action if set to False?
        self.expectedParameters['femFastCtrlDynamic']           = AttributeContainer(bool, 'FemFastCtrlDynamic', 'Enables fast control with dynamic vetos',
                                                                      (True, False), None, True,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['femEnableTenGig']              = AttributeContainer(bool, 'FemEnableTenGig', 'Enables transmission of image data via 10GigE UDP interface',
                                                                      (True, False), None, True,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['femDataSource']                = AttributeContainer(int, 'FemDataSource', 'Source of data sent to 10GigE: 0=ASIC (via PPC), 1=ASIC (from Rxblock), 2=frame generator, 3=PPC (preprogrammed)',
                                                                      0, 3, 1,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
#        self.expectedParameters['femAsicEnableMask']            = AttributeContainer([int]*4, 'FemAsicEnableMask', 'ASIC RX channel enable mask (4*32 bits)',
#                                                                         0, 0xFFFFFFFF, [0xFFFFFFFF]*4,
#                                                                         AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        self.expectedParameters['femAsicEnableMask']            = AttributeContainer(int, 'FemAsicEnableMask', 'ASIC RX channel enable mask (4*32 bits)',
                                                                         0, 0xFFFFFFFF, 99999999,
                                                                         AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['femAsicColumns']               = AttributeContainer(int, 'FemAsicColumns', 'Sets ASIC RX readout size (time-slices) per trigger',
                                                                         0, 255, 1,
                                                                         AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['femAsicGainOverride']          = AttributeContainer(int, 'FemAsicGainOverride', 'Overrides ASIC gain selection algorithm (0=normal, 8=x100, 9=x10, 11=x1',
                                                                         (0, 8, 9, 11), None, 0,
                                                                         AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['femAsicSlowControlParams']     = AttributeContainer(str, 'FemAsicSlowControlParams', 'ASIC slow control parameter definition in XML syntax',
                                                                            None, None, 'asicSlowControl.xml',
                                                                            AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['femAsicFastCmdSequence']       = AttributeContainer(str, 'FemAsicFastCmdSequence', 'ASIC fast command (readout) sequence definition in XML syntax',
                                                                          None, None, 'asicFastCommandSequence.xml',
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['femAsicPixelFeedbackOverride'] = AttributeContainer(int, 'FemAsicPixelFeedbackOverride', 'ASIC per-pixel override of feedback selection: 0 = high(10p), 1= low(50p)',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam ,'AllOk.Idle')
        
        self.expectedParameters['femAsicPixelSelfTestOverride'] = AttributeContainer(int, 'FemAsicPixelSelfTestOverride', 'ASIC per-pixel override of self-test enable: 1 = enabled',
                                                                          0, 1, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['femReadoutOperatingMode']      = AttributeContainer(int, 'FemReadoutOperatingMode', 'FEM readout operating mode (e.g. normal, self-test scan etc, TBD',
                                                                          0, 255, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        ############ Additional Variables ############
    
        self.expectedParameters['femAsicDataType']      = AttributeContainer(int, 'FemAsicDataType', 'ASIC data type 0=sensor data, 1=rx counting, 2=pseudorandom',
                                                                          0, 2, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femAsicLocalClock']    = AttributeContainer(int, 'FemAsicLocalClock', 'ASIC clock scaling 0=100 MHz, 1=scaled down clock (10 MHz)',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femAsicSlowLoadMode']  = AttributeContainer(int, 'FemAsicSlowLoadMode', 'ASIC control load mode 0=parallel, 1=serial',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femAsicRxInvertData']  = AttributeContainer(bool, 'FemAsicRxInvertData', 'Invert ADC ASIC data',
                                                                          (True, False), None, False,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femAsicRxFastStrobe']  = AttributeContainer(bool, 'FemAsicRxFastStrobe', 'Start ASIC capture using strobe derived from ASIC Command file',
                                                                          (True, False), None, True,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femAsicRxDelayOddChannels'] = AttributeContainer(bool, 'FemAsicRxDelayOddChannels', 'Delay odd ASIC data channels by one clock to fix alignment',
                                                                          (True, False), None, True,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femAsicSlowClockPhase']= AttributeContainer(int, 'FemAsicSlowClockPhase', 'ASIC additional phase adjustment of slow clock rsync wrt ASIC reset',
                                                                          0, 65535, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femAsicSlowedClock']   = AttributeContainer(bool, 'FemAsicSlowedClock', 'ASIC readout phase is slowed down',
                                                                          (True, False), None, False,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femPpcMode']           = AttributeContainer(int, 'FemPpcMode', 'Fem PPC mode 0=single train shot with PPC reset, 1=Continuous readout',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femPpcResetDelay']     = AttributeContainer(int, 'FemPpcResetDelay', 'Delay after resetting ppc ',
                                                                          0, 10, 5,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femNumTestCycles']     = AttributeContainer(int, 'FemNumTestCycles', 'Number of test cycles if LL Data Generator or PPC Data Direct selected',
                                                                          0, 255, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['tenGigFarmMode']       = AttributeContainer(int, 'TenGigFarmMode', '10GigE farm mode 1=disabled, 2=fixed IP,multi port, 3=farm mode with nic lists',
                                                                          1, 3, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femI2cBus']            = AttributeContainer(int, 'FemI2cBus', 'Set Fem i2c internal bus 0x000=LM82, 0x100=EEPROM, 0x200=RHS Power Card, 0x300=LHS Power Card (2Tile System)',
                                                                          (0x000,  0x100, 0x200, 0x300), None, 0x300,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femAsicVersion']      = AttributeContainer(int, 'FemAsicVersion', 'ASIC version 1=version 1, 2=version 2',
                                                                          1, 2, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femAsicClockSource']    = AttributeContainer(int, 'FemAsicClockSource', 'ASIC clock source 0=Fem local oscillator, 1=XFEL C&C System',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

        self.expectedParameters['femDebugLevel']    = AttributeContainer(int, 'FemDebugLevel', 'Set the debug level',
                                                                          0, 6, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        #TODO: Decide range of values?
        self.expectedParameters['tenGig0DataGenerator']    = AttributeContainer(int, 'TenGig0DataGenerator', '10GigE 0 Data generator 1=DataGen 2=PPC DDR2',
                                                                          1, 2, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        #TODO: Decide range of values?
        self.expectedParameters['tenGig0DataFormat']    = AttributeContainer(int, 'TenGig0DataFormat', '10GigE 0 Data format type 0=counting data',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        #TODO: Decide range of values?
        self.expectedParameters['tenGig0FrameLength']    = AttributeContainer(int, 'TenGig0FrameLength', '10GigE 0 Frame length in bytes',
                                                                          0, 0xFFFFFF, 0x10000,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        #TODO: Decide range of values?
        self.expectedParameters['tenGig0NumberOfFrames']    = AttributeContainer(int, 'TenGig0NumberOfFrames', '10GigE 0 Number of frames to send in each cycle',
                                                                          0, 512, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')

    
    def get(self):
        '''
        Returns an ordered dictionary of the expected parameters built by the constructor
        '''
        return self.expectedParameters
    
    def parameterTemplateStr(self, schemaName):
        '''
        Generator for building (incomplete) Karabo schema definitions for parameters. This 
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
        for param, attrib in self.expectedParameters.iteritems():
    
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
            
            # Insert allowed states if the parameter is reconfigurable
            if attrib.accessType == AccessWrite:
                templateStr += 'e.allowedStates(' + repr(attrib.allowedStates) + ")\n"
            
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
