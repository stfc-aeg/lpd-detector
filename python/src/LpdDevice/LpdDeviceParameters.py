'''
Created on 25 Sep 2012

@author: tcn
'''

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
    
        self.parameters = { 
                            #
                            # Power card control parameters
                            #
                            'sensorBias'       : AttributeContainer(float, 'SensorBias', 'Sensor HV Bias Voltage [V]', 
                                                                      0, 500, 0,
                                                                      AccessWrite, True, 'volt', 'V' ),
                            'sensorBiasEnable' : AttributeContainer(bool, 'SensorBiasEnable', 'Sensor HV Bias Enable', 
                                                                      (True, False), None, False,
                                                                      AccessWrite, AssignmentOptional),
                            'asicPowerEnable'    : AttributeContainer(bool, 'AsicPowerEnable', 'ASIC LV Power Enable', 
                                                                      (True, False), None, False,
                                                                      AccessWrite, AssignmentOptional),
                            #
                            # Power card monitoring parameters
                            #
                            'powerCardFault'     : AttributeContainer(bool, 'PowerCardFault', 'Power Card Fault Flag', 
                                                                      (True, False), None, None,
                                                                      AccessRead, AssignmentOptional),
                            'powerCardFemStatus' : AttributeContainer(bool, 'PowerCardFemStatus', 'Power Card FEM Status Flag',
                                                                      (True, False), None, None,
                                                                      AccessRead, AssignmentOptional),
                            'powerCardExtStatus' : AttributeContainer(bool, 'PowerCardExtStatus', 'Power Card External Status Flag',
                                                                      (True, False), None, None,
                                                                      AccessRead, AssignmentOptional),
                            'powerCardOverCurrent' : AttributeContainer(bool, 'PowerCardOvercurrent', 'Power Card Overcurrent Flag',
                                                                      (True, False), None, None,
                                                                      AccessRead, AssignmentOptional),
                            'powerCardOvertemp' : AttributeContainer(bool, 'PowerCardOverTemp', 'Power Card Over Temperature Flag',
                                                                      (True, False), None, None,
                                                                      AccessRead, AssignmentOptional),
                            'powerCardUndertemp' : AttributeContainer(bool, 'PowerCardUnderTemp', 'Power Card Under Temperature Flag',
                                                                      (True, False), None, None,
                                                                      AccessRead, None),
                            'powerCardTemp'      : AttributeContainer(float, 'PowerCardTemp', 'Power Card Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C'),
                            'sensorATemp'        : AttributeContainer(float, 'SensorATemp', 'Sensor A Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C'),
                            'sensorBTemp'        : AttributeContainer(float, 'SensorBTemp', 'Sensor B Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C'),
                            'sensorCTemp'        : AttributeContainer(float, 'SensorCTemp', 'Sensor C Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C'),
                            'sensorDTemp'        : AttributeContainer(float, 'SensorDTemp', 'Sensor D Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C'),
                            'sensorETemp'        : AttributeContainer(float, 'SensorETemp', 'Sensor E Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C'),
                            'sensorFTemp'        : AttributeContainer(float, 'SensorFTemp', 'Sensor F Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C'),
                            'sensorGTemp'        : AttributeContainer(float, 'SensorGTemp', 'Sensor G Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C'),
                            'sensorHTemp'        : AttributeContainer(float, 'SensorHTemp', 'Sensor H Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, 'Celsius', 'C'),
                            'femVoltage'         : AttributeContainer(float, 'FemVoltage', 'FEM 5V Supply Voltage [V]',
                                                                      0, 6,  None,
                                                                      AccessRead, None, 'Volts', 'V'),
                            'femCurrent'         : AttributeContainer(float, 'FemCurrent', 'FEM 5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A'),
                            'digitalVoltage'     : AttributeContainer(float, 'DigitalVoltage', 'ASIC 1.2V Digital Supply Voltage [V]',
                                                                      0, 2,  None,
                                                                      AccessRead, None, 'Volts', 'V'),
                            'digitalCurrent'     : AttributeContainer(float, 'DigitalVoltage', 'ASIC 1.2V Digital Supply Current [mA]',
                                                                      0, 1000,  None,
                                                                      AccessRead, None, 'Milliamps', 'mA'),
                            'sensorAVoltage'     : AttributeContainer(float, 'SensorAVoltage', 'Sensor A 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V'),
                            'sensorACurrent'     : AttributeContainer(float, 'SensorACurrent', 'Sensor A 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A'),
                            'sensorBVoltage'     : AttributeContainer(float, 'SensorBVoltage', 'Sensor B 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V'),
                            'sensorBCurrent'     : AttributeContainer(float, 'SensorBCurrent', 'Sensor B 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A'),
                            'sensorCVoltage'     : AttributeContainer(float, 'SensorCVoltage', 'Sensor C 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V'),
                            'sensorCCurrent'     : AttributeContainer(float, 'SensorCCurrent', 'Sensor C 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A'),
                            'sensorDVoltage'     : AttributeContainer(float, 'SensorDVoltage', 'Sensor D 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V'),
                            'sensorDCurrent'     : AttributeContainer(float, 'SensorDCurrent', 'Sensor D 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A'),
                            'sensorEVoltage'     : AttributeContainer(float, 'SensorEVoltage', 'Sensor E 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V'),
                            'sensorECurrent'     : AttributeContainer(float, 'SensorECurrent', 'Sensor E 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A'),
                            'sensorFVoltage'     : AttributeContainer(float, 'SensorFVoltage', 'Sensor F 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V'),
                            'sensorFCurrent'     : AttributeContainer(float, 'SensorFCurrent', 'Sensor F 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A'),
                            'sensorGVoltage'     : AttributeContainer(float, 'SensorGVoltage', 'Sensor G 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V'),
                            'sensorGCurrent'     : AttributeContainer(float, 'SensorGCurrent', 'Sensor G 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A'),
                            'sensorHVoltage'     : AttributeContainer(float, 'SensorHVoltage', 'Sensor H 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, 'Volts', 'V'),
                            'sensorHCurrent'     : AttributeContainer(float, 'SensorHCurrent', 'Sensor H 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, 'Amps', 'A'),
                            'sensorBiasVoltage'  : AttributeContainer(float, 'SensorBiasVoltage', 'Sensor bias voltage readback [V]',
                                                                      0, 600, None,
                                                                      AccessRead, None, 'Volts', 'V'),
                            'sensorBiasCurrent'  : AttributeContainer(float, 'SensorBiasVoltage', 'Sensor bias current readback [uA]',
                                                                      0, 600, None,
                                                                      AccessRead, None, 'Microamps', 'uA'),

                            #
                            # TenGig Ethernet UDP Parameters - two 10GiGE interfaces
                            #
                            'tenGig0SourceMac'   : AttributeContainer(str, 'TenGigE0SourceMAC', '10GigE 0 UDP Source MAC Address',
                                                                      '', '', '62-00-00-00-00-01',
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGig0SourceIp'    : AttributeContainer(str, 'TenGigE0SourceIp', '10GigE 0 UDP Source IP Address',
                                                                      '', '', '10.0.1.1',
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGig0SourcePort'  : AttributeContainer(int, 'TenGigE0SourcePort', '10GigE 0 UDP Source Port',
                                                                      0, 65535, 8,
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGig0DestMac'     : AttributeContainer(str, 'TenGigE0DestMAC', '10GigE 0 UDP Destination MAC Address',
                                                                      '', '', '00-07-43-01-01-01',
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGig0DestIp'      : AttributeContainer(str, 'TenGigE0DestIp', '10GigE 0 UDP Destination IP Address',
                                                                      '', '', '10.0.1.2',
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGig0DestPort'    : AttributeContainer(int, 'TenGigE0DestPort', '10GigE 0 UDP Destination Port',
                                                                      0, 65535, 61649,
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGig1SourceMac'   : AttributeContainer(str, 'TenGigE1SourceMAC', '10GigE 1 UDP Source MAC Address',
                                                                      '', '', '62-00-00-00-00-02',
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGig1SourceIp'    : AttributeContainer(str, 'TenGigE1SourceIp', '10GigE 1 UDP Source IP Address',
                                                                      '', '', '10.0.2.1',
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGig1SourcePort'  : AttributeContainer(int, 'TenGigE1SourcePort', '10GigE 1 UDP Source Port',
                                                                      0, 65535, 8,
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGig1DestMac'     : AttributeContainer(str, 'TenGigE1DestMAC', '10GigE 1 UDP Destination MAC Address',
                                                                      '', '', '00-07-43-01-01-02',
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGig1DestIp'      : AttributeContainer(str, 'TenGigE1DestIp', '10GigE 1 UDP Destination IP Address',
                                                                      '', '', '10.0.2.2',
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGig1DestPort'    : AttributeContainer(int, 'TenGigE1DestPort', '10GigE 1 UDP Destination Port',
                                                                      0, 65535, 61649,
                                                                      AccessWrite, AssignmentMandatory),
                            'tenGigInterframeGap' : AttributeContainer(int, 'TenGigInterframeGap', '10GigE Inter-frame gap timer [clock cycles]',
                                                                      0, 0xFFFFFFFF, 0x1000,
                                                                      AccessWrite, AssignmentOptional),
                            'tenGigUdpPacketLen'  : AttributeContainer(int, 'TenGigUDPPacketLength', '10GigE UDP packet payload length',
                                                                      0, 65535, 8000,
                                                                      AccessWrite, AssignmentOptional),
                           
                            #
                            # LPD FEM firmware block parameters. Note these are simply based on all exposed
                            # parameters in the original test scripts - many may be replaced or hard-coded in
                            # production firmware iterations
                            #
                            'femSendPpcReset'     : AttributeContainer(bool, 'FemSendPPCReset', 'Send PPC processor reset to FEM',
                                                                      (True, False), None, True,
                                                                      AccessWrite, AssignmentOptional),
                            'femFastCtrlDynamic'  : AttributeContainer(bool, 'FemFastCtrlDynamic', 'Enables fast control with dynamic vetos',
                                                                      (True, False), None, True,
                                                                      AccessWrite, AssignmentOptional),
                            'femSetupSlowCtrlBram' : AttributeContainer(bool, 'FemSetupSlowCtrlBRAM', 'Enables setup of ASIC slow control sequence',
                                                                      (True, False), None, True,
                                                                      AccessWrite, AssignmentOptional),
                            'femEnableTenGig'      : AttributeContainer(bool, 'FemEnableTenGig', 'Enables transmission of image data via 10GigE UDP interface',
                                                                      (True, False), None, True,
                                                                      AccessWrite, AssignmentOptional),
                            'femDataSource'        : AttributeContainer(int, 'FemDataSource', 'Source of data sent to 10GigE: 0=frame generator, 1=ASIC, 2=PPC',
                                                                      0, 2, 1,
                                                                      AccessWrite, AssignmentOptional),
                            'femAsicCountingData'  : AttributeContainer(bool, 'FemAsicCountingData', 'Enables dummy ASIC counting data in FEM',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional),
                            'femAsicModuleType'    : AttributeContainer(int, 'FemAsicModuleType', 'Selects type of ASIC module 1=single ASIC, 2=2-tile module',
                                                                        1, 2, 2,
                                                                        AccessWrite, AssignmentOptional),
                            'femAsicRxStartDelay'  : AttributeContainer(int, 'FemAsicRxStartDelay', 'Number of clock periods before start of ASIC data RX - will be replaced',
                                                                        0, 65535, 61,
                                                                        AccessWrite, AssignmentOptional),
                            'femNumLocalLinkFrames' : AttributeContainer(int, 'FemNumLocalLinkFrames', 'Number of local link frames to generate in test mode',
                                                                         0, 65536, 1,
                                                                         AccessWrite, AssignmentOptional),
                            'femAsicFastCmdRegSize' : AttributeContainer(int, 'FemAsicFastCmdRegSize', 'Size of the ASIC fast command register in bits',
                                                                         (20, 22), None, 22,
                                                                         AccessWrite, AssignmentOptional),
                            'femAsicEnableMask'     : AttributeContainer([int], 'FemAsicEnableMask', 'ASIC RX channel enable mask (4*32 bits)',
                                                                         0, 0xFFFFFFFF, 0,
                                                                         AccessWrite, AssignmentMandatory),
                            'femAsicColumns'        : AttributeContainer(int, 'FemAsicColumns', 'Sets ASIC RX readout size (time-slices) per trigger',
                                                                         0, 255, 1,
                                                                         AccessWrite, AssignmentOptional),
                            'femAsicColumnsPerFrame' : AttributeContainer(int, 'FemAsicColumnsPerFrame', 'Sets ASIC readout size per output frame',
                                                                         0, 255, 1,
                                                                         AccessWrite, AssignmentOptional),
                            'femAsicGainOverride'   : AttributeContainer(int, 'FemAsicGainOverride', 'Overrides ASIC gain selection algorithm (0=normal, 8=x100, 9=x10, 11=x1',
                                                                         (0, 8, 9, 11), None, 0,
                                                                         AccessWrite, AssignmentOptional),
                            'femAsicSlowControlParams' : AttributeContainer(str, 'FemAsicSlowControlParams', 'ASIC slow control parameter definition in XML syntax',
                                                                            None, None, None,
                                                                            AccessWrite, AssignmentMandatory),
                            'femAsicFastCmdSequence' : AttributeContainer(str, 'FemAsicFastCmdSequence', 'ASIC fast command (readout) sequence definition in XML syntax',
                                                                          None, None, None,
                                                                          AccessWrite, AssignmentMandatory),
                            'femAsicPixelFeedbackOverride' : AttributeContainer(int, 'FemAsicPixelFeedbackOverride', 'ASIC per-pixel override of feedback selection: 0 = high(10p), 1= low(50p)',
                                                                          0, 1, None,
                                                                          AccessWrite, AssignmentOptional),
                            'femAsicPixelSelfTestOverride' : AttributeContainer(int, 'FemAsicPixelSelfTestOverride', 'ASIC per-pixel override of self-test enable: 1 = enabled',
                                                                          0, 1, None,
                                                                          AccessWrite, AssignmentOptional),
                            'femReadoutOperatingMode'      : AttributeContainer(int, 'FemReadoutOperatingMode', 'FEM readout operating mode (e.g. normal, self-test scan etc, TBD',
                                                                          0, 255, 0,
                                                                          AccessWrite, AssignmentOptional),
                           }        
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
                             'float'  : 'FLOAT_ELEMENT',
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
