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

# Wrapper classes to allow Python native int parameters to be mapped onto Karabo int types
class int32(int):
    pass

class int64(int):
    pass

class uint32(int):
    pass

class uint64(int):
    pass

class AttributeContainer(object):

    '''
    Simple class to provide structured container for parameter attributes. It is designed
    to simply enforce a consistent description of the required attributes a device
    parameter must possess, as defined by the Karabo parameter schema
    '''
        
    def __init__(self, paramType, displayedName, description, minValueOrRange, maxValue, defaultValue,
                   accessType, assignmentPolicy, isInternal, allowedStates, tags=None, unitName=None, unitSymbol=None):
        
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
        self.tags             = tags
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
        #           tags, unit name, unit symbol )
    
        self.expectedParameters = OrderedDict()

        # Internal parameters used in the LpdDevice class but not passed down into the underlying client object
        
        self.expectedParameters['femHost']           = AttributeContainer(str, 'FEM Host', 'FEM hostname or IP address',
                                                                    None, None, '127.0.0.1',
                                                                    AccessWrite, AssignmentOptional, InternalParam, 
                                                                    'AllOk.Disconnected')
        self.expectedParameters['femPort']           = AttributeContainer(uint32, 'FEM Port', 'FEM port number',
                                                                    0, 65535, 6969,
                                                                    AccessWrite, AssignmentOptional, InternalParam,
                                                                    'AllOk.Disconnected')
        self.expectedParameters['femTimeout']        = AttributeContainer(uint32, 'FEM Timeout', 'FEM connection timeout',
                                                                    0, 1000, 30,
                                                                    AccessWrite, AssignmentOptional, InternalParam,
                                                                    'AllOk.Disconnected')
        self.expectedParameters['femAsicModuleType'] = AttributeContainer(uint32, 'FemAsicModuleType', 
                                                                    'Selects ASIC module type 0=Supermodule, 1=Single ASIC, 2=2-tile module, 3=Stand-alone',
                                                                    0, 3, 0,
                                                                    AccessWrite, AssignmentOptional, InternalParam, 
                                                                    'AllOk.Disconnected')

        #
        # Power card control parameters
        #
        
        self.expectedParameters['sensorBias0']           = AttributeContainer(float, 'SensorBias0', 'Sensor 0 HV Bias Voltage [V]',
                                                                        0, 500, 0,
                                                                        AccessWrite, True, ExternalParam, 
                                                                        'AllOk.Idle', "once, set, composite", 'Volt', 'V' )
        
        self.expectedParameters['sensorBias1']           = AttributeContainer(float, 'SensorBias1', 'Sensor 1 HV Bias Voltage [V]',
                                                                        0, 500, 0,
                                                                        AccessWrite, True, ExternalParam, 
                                                                        'AllOk.Idle', "once, set, composite", 'volt', 'V' )
        
        self.expectedParameters['sensorBiasEnable0']     = AttributeContainer(bool, 'SensorBiasEnable0', 'Sensor 0 HV Bias Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional, ExternalParam,
                                                                        'AllOk.Idle', "once, set, composite")
        
        self.expectedParameters['sensorBiasEnable1']     = AttributeContainer(bool, 'SensorBiasEnable1', 'Sensor 1 HV Bias Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional, ExternalParam,
                                                                        'AllOk.Idle', "once, set, composite")
        
        self.expectedParameters['asicPowerEnable0']      = AttributeContainer(bool, 'AsicPowerEnable0', 'ASIC 0 LV Power Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional, ExternalParam,
                                                                        'AllOk.Idle', "once, set, composite")

        self.expectedParameters['asicPowerEnable1']      = AttributeContainer(bool, 'AsicPowerEnable1', 'ASIC 1 LV Power Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional, ExternalParam,
                                                                        'AllOk.Idle', "once, set, composite")
            
        #
        # Power card monitoring parameters
        #
        
        self.expectedParameters['powerCardFault0']       = AttributeContainer(bool, 'PowerCardFault0', 'Power Card 0 Fault Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardFault1']       = AttributeContainer(bool, 'PowerCardFault1', 'Power Card 1 Fault Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardFemStatus0']   = AttributeContainer(bool, 'PowerCardFemStatus0', 'Power Card 0 FEM Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardFemStatus1']   = AttributeContainer(bool, 'PowerCardFemStatus1', 'Power Card 1 FEM Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardExtStatus0']   = AttributeContainer(bool, 'PowerCardExtStatus0', 'Power Card 0 External Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardExtStatus1']   = AttributeContainer(bool, 'PowerCardExtStatus1', 'Power Card 1 External Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardOverCurrent0'] = AttributeContainer(bool, 'PowerCardOverCurrent0', 'Power Card 0 Overcurrent Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardOverCurrent1'] = AttributeContainer(bool, 'PowerCardOverCurrent1', 'Power Card 1 Overcurrent Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardOverTemp0']    = AttributeContainer(bool, 'PowerCardOverTemp0', 'Power Card Over 0 Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardOverTemp1']    = AttributeContainer(bool, 'PowerCardOverTemp1', 'Power Card Over 1 Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardUnderTemp0']   = AttributeContainer(bool, 'PowerCardUnderTemp0', 'Power Card Under 0 Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardUnderTemp1']   = AttributeContainer(bool, 'PowerCardUnderTemp1', 'Power Card Under 1 Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None, "poll")
        
        self.expectedParameters['powerCardTemp0']        = AttributeContainer(float, 'PowerCardTemp0', 'Power Card 0 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['powerCardTemp1']        = AttributeContainer(float, 'PowerCardTemp1', 'Power Card 1 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor0Temp']           = AttributeContainer(float, 'Sensor0Temp', 'Sensor 0 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor1Temp']           = AttributeContainer(float, 'Sensor1Temp', 'Sensor 1 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
                            
        self.expectedParameters['sensor2Temp']           = AttributeContainer(float, 'Sensor2Temp', 'Sensor 2 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor3Temp']           = AttributeContainer(float, 'Sensor3Temp', 'Sensor 3 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor4Temp']           = AttributeContainer(float, 'Sensor4Temp', 'Sensor 4 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor5Temp']           = AttributeContainer(float, 'Sensor5Temp', 'Sensor 5 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor6Temp']           = AttributeContainer(float, 'Sensor6Temp', 'Sensor 6 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor7Temp']           = AttributeContainer(float, 'Sensor7Temp', 'Sensor 7 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor8Temp']           = AttributeContainer(float, 'Sensor8Temp', 'Sensor 8 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor9Temp']           = AttributeContainer(float, 'Sensor9Temp', 'Sensor 9 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
                            
        self.expectedParameters['sensor10Temp']          = AttributeContainer(float, 'Sensor10Temp', 'Sensor 10 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor11Temp']          = AttributeContainer(float, 'Sensor11Temp', 'Sensor 11 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor12Temp']          = AttributeContainer(float, 'Sensor12Temp', 'Sensor 12 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor13Temp']          = AttributeContainer(float, 'Sensor13Temp', 'Sensor 13 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor14Temp']          = AttributeContainer(float, 'Sensor14Temp', 'Sensor 14 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['sensor15Temp']          = AttributeContainer(float, 'Sensor15Temp', 'Sensor 15 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Celsius', 'C')
        
        self.expectedParameters['femVoltage0']           = AttributeContainer(float, 'FemVoltage0', 'FEM 5V Supply 0 Voltage [V]',
                                                                        0, 6,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['femVoltage1']           = AttributeContainer(float, 'FemVoltage1', 'FEM 5V Supply 1 Voltage [V]',
                                                                        0, 6,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['femCurrent0']           = AttributeContainer(float, 'FemCurrent0', 'FEM 5V Supply 0 Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['femCurrent1']           = AttributeContainer(float, 'FemCurrent1', 'FEM 5V Supply 1 Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['digitalVoltage0']       = AttributeContainer(float, 'DigitalVoltage0', 'ASIC 1.2V Digital Supply 0 Voltage [V]',
                                                                        0, 2,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['digitalVoltage1']       = AttributeContainer(float, 'DigitalVoltage1', 'ASIC 1.2V Digital Supply 1 Voltage [V]',
                                                                        0, 2,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')

        self.expectedParameters['digitalCurrent0']       = AttributeContainer(float, 'DigitalCurrent0', 'ASIC 1.2V Digital Supply 0 Current [mA]',
                                                                        0, 1000,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Milliamp', 'mA')
        
        self.expectedParameters['digitalCurrent1']       = AttributeContainer(float, 'DigitalCurrent1', 'ASIC 1.2V Digital Supply 1 Current [mA]',
                                                                        0, 1000,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Milliamp', 'mA')
        
        self.expectedParameters['sensor0Voltage']        = AttributeContainer(float, 'Sensor0Voltage', 'Sensor 0 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor1Voltage']        = AttributeContainer(float, 'Sensor1Voltage', 'Sensor 1 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
                            
        self.expectedParameters['sensor2Voltage']        = AttributeContainer(float, 'Sensor2Voltage', 'Sensor 2 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor3Voltage']        = AttributeContainer(float, 'Sensor3Voltage', 'Sensor 3 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor4Voltage']        = AttributeContainer(float, 'Sensor4Voltage', 'Sensor 4 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor5Voltage']        = AttributeContainer(float, 'Sensor5Voltage', 'Sensor 5 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor6Voltage']        = AttributeContainer(float, 'Sensor6Voltage', 'Sensor 6 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor7Voltage']        = AttributeContainer(float, 'Sensor7Voltage', 'Sensor 7 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor8Voltage']        = AttributeContainer(float, 'Sensor8Voltage', 'Sensor 8 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor9Voltage']        = AttributeContainer(float, 'Sensor9Voltage', 'Sensor 9 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
                            
        self.expectedParameters['sensor10Voltage']       = AttributeContainer(float, 'Sensor10Voltage', 'Sensor 10 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor11Voltage']       = AttributeContainer(float, 'Sensor11Voltage', 'Sensor 11 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor12Voltage']       = AttributeContainer(float, 'Sensor12Voltage', 'Sensor 12 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor13Voltage']       = AttributeContainer(float, 'Sensor13Voltage', 'Sensor 13 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor14Voltage']       = AttributeContainer(float, 'Sensor14Voltage', 'Sensor 14 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor15Voltage']       = AttributeContainer(float, 'Sensor15Voltage', 'Sensor 15 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensor0Current']        = AttributeContainer(float, 'Sensor0Current', 'Sensor 0 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor1Current']        = AttributeContainer(float, 'Sensor1Current', 'Sensor 1 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
                            
        self.expectedParameters['sensor2Current']        = AttributeContainer(float, 'Sensor2Current', 'Sensor 2 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor3Current']        = AttributeContainer(float, 'Sensor3Current', 'Sensor 3 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor4Current']        = AttributeContainer(float, 'Sensor4Current', 'Sensor 4 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor5Current']        = AttributeContainer(float, 'Sensor5Current', 'Sensor 5 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor6Current']        = AttributeContainer(float, 'Sensor6Current', 'Sensor 6 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor7Current']        = AttributeContainer(float, 'Sensor7Current', 'Sensor 7 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor8Current']        = AttributeContainer(float, 'Sensor8Current', 'Sensor 8 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor9Current']        = AttributeContainer(float, 'Sensor9Current', 'Sensor 9 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
                            
        self.expectedParameters['sensor10Current']       = AttributeContainer(float, 'Sensor10Current', 'Sensor 10 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor11Current']       = AttributeContainer(float, 'Sensor11Current', 'Sensor 11 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor12Current']       = AttributeContainer(float, 'Sensor12Current', 'Sensor 12 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor13Current']       = AttributeContainer(float, 'Sensor13Current', 'Sensor 13 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor14Current']       = AttributeContainer(float, 'Sensor14Current', 'Sensor 14 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensor15Current']       = AttributeContainer(float, 'Sensor15Current', 'Sensor 15 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Amp', 'A')
        
        self.expectedParameters['sensorBiasVoltage0']    = AttributeContainer(float, 'SensorBiasVoltage0', 'Sensor bias 0 voltage readback [V]',
                                                                        0, 300, None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensorBiasVoltage1']    = AttributeContainer(float, 'SensorBiasVoltage1', 'Sensor bias 1 voltage readback [V]',
                                                                        0, 300, None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Volt', 'V')
        
        self.expectedParameters['sensorBiasCurrent0']    = AttributeContainer(float, 'SensorBiasCurrent0', 'Sensor bias 0 current readback [uA]',
                                                                        0, 600, None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Microamp', 'uA')

        self.expectedParameters['sensorBiasCurrent1']    = AttributeContainer(float, 'SensorBiasCurrent1', 'Sensor bias 1 current readback [uA]',
                                                                        0, 600, None,
                                                                        AccessRead, None, ExternalParam, None, "poll", 'Microamp', 'uA')

        #
        # TenGig Ethernet UDP Parameters - one 10GiGE interface
        #
                            
        self.expectedParameters['tenGig0SourceMac']     = AttributeContainer(str, 'TenGigE0SourceMAC', '10GigE 0 UDP Source MAC Address',
                                                                      None, None, '62-00-00-00-00-01',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['tenGig0SourceIp']      = AttributeContainer(str, 'TenGigE0SourceIp', '10GigE 0 UDP Source IP Address',
                                                                      None, None, '10.0.0.2',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['tenGig0SourcePort']    = AttributeContainer(uint32, 'TenGigE0SourcePort', '10GigE 0 UDP Source Port',
                                                                      0, 65535, 0,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['tenGig0DestMac']       = AttributeContainer(str, 'TenGigE0DestMAC', '10GigE 0 UDP Destination MAC Address',
                                                                      None, None, '00-07-43-10-65-A0',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['tenGig0DestIp']        = AttributeContainer(str, 'TenGigE0DestIp', '10GigE 0 UDP Destination IP Address',
                                                                      None, None, '10.0.0.1',
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['tenGig0DestPort']      = AttributeContainer(uint32, 'TenGigE0DestPort', '10GigE 0 UDP Destination Port',
                                                                      0, 65535, 61649,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
                
        self.expectedParameters['tenGigInterframeGap']  = AttributeContainer(uint32, 'TenGigInterframeGap', '10GigE Inter-frame gap timer [clock cycles]',
                                                                      0, 0xFFFFFFFF, 0x0,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['tenGigUdpPacketLen']   = AttributeContainer(uint32, 'TenGigUDPPacketLength', '10GigE UDP packet payload length',
                                                                      0, 65535, 8000,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set, composite")
                           
        #
        # LPD FEM firmware block parameters. Note these are simply based on all exposed
        # parameters in the original test scripts - many may be replaced or hard-coded in
        # production firmware iterations
        #
        
        self.expectedParameters['femEnableTenGig']              = AttributeContainer(bool, 'FemEnableTenGig', 'Enables transmission of image data via 10GigE UDP interface',
                                                                      (True, False), None, True,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['femDataSource']                = AttributeContainer(uint32, 'FemDataSource', 'Source of data sent to 10GigE: 0=ASIC (via PPC), 1=ASIC (bypassing PPC), 2=Frame Generator, 3=PPC (pattern data)',
                                                                      0, 3, 0,
                                                                      AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['femAsicEnableMask']            = AttributeContainer([uint32]*4, 'FemAsicEnableMask', 'ASIC RX channel enable mask (4*32 bits)',
                                                                         0, 0xFFFFFFFF, [0xFFFFFFFF]*4,
                                                                         AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle')
        
        self.expectedParameters['numberImages']                 = AttributeContainer(uint32, 'NumberImages', 'Sets the number of images per trigger',
                                                                         0, 511, 4,
                                                                         AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set, composite")
        
        self.expectedParameters['integrationCycles']            = AttributeContainer(uint32, 'integrationCycles', 'Sets the number of integration cycles per images',
                                                                         0, 100, 1,
                                                                         AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set, composite")
        
        self.expectedParameters['femAsicGain']                  = AttributeContainer(uint32, 'FemAsicGain', 'Set the ASIC gain selection mode (0=ASIC algorithm, 3=x100, 2=x10, 1=x1)',
                                                                         (0, 3, 2, 1), None, 0,
                                                                         AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set, composite")
        
        self.expectedParameters['femAsicSetupParams']           = AttributeContainer(str, 'FemAsicSetupParams', 'ASIC Setup Parameters defined in XML syntax',
                                                                          None, None, 'asicSlowControl.xml',
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set, composite")
        
        self.expectedParameters['femAsicCmdSequence']           = AttributeContainer(str, 'FemAsicCmdSequence', 'ASIC Command Words defined in XML syntax',
                                                                          None, None, 'asicFastCommandSequence.xml',
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set, composite")
        
        self.expectedParameters['femAsicPixelFeedbackOverride'] = AttributeContainer(int32, 'FemAsicPixelFeedbackOverride', 'ASIC pixel feedback override selection: 0=low(50pF), 1=high(5pF), -1=XML decides',
                                                                          -1, 1, -1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam ,'AllOk.Idle', "once, set, composite")
        
        self.expectedParameters['femAsicPixelSelfTestOverride'] = AttributeContainer(int32, 'FemAsicPixelSelfTestOverride', 'ASIC pixel self-test override selection: 0=off, 1-5=test selection, -1=XML decides',
                                                                          -1, 5, -1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        #TODO: Not yet Implemented
        self.expectedParameters['femReadoutOperatingMode']      = AttributeContainer(uint32, 'FemReadoutOperatingMode', 'FEM readout operating mode (e.g. Normal, Self-test scan etc, TBD',
                                                                          0, 255, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        ############ Additional Variables ############
    
        self.expectedParameters['femAsicDataType']              = AttributeContainer(uint32, 'FemAsicDataType', 'ASIC data type 0=Sensor data, 1=FEM internal counting, 2=ASIC pseudorandom',
                                                                          0, 2, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femAsicLocalClock']            = AttributeContainer(uint32, 'FemAsicLocalClock', 'ASIC clock scaling 0=100 MHz (no scaling), 1=Scaled down clock (10 MHz)',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femAsicSetupLoadMode']         = AttributeContainer(uint32, 'FemAsicSetupLoadMode', 'ASIC control load mode 0=parallel, 1=serial (being tested)',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femInvertAdcData']             = AttributeContainer(bool, 'FemInvertAdcData', 'Enable Invert ADC ASIC data True=Invert Data',
                                                                          (True, False), None, False,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femAsicRxCmdWordStart']        = AttributeContainer(bool, 'FemAsicRxCmdWordStart', 'Enable ASIC readout started by Command Word in femAsicCmdSequence file',
                                                                          (True, False), None, True,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femAsicSetupClockPhase']       = AttributeContainer(uint32, 'FemAsicSetupClockPhase', 'ASIC Setup Params additional phase adjustment of clock rsync wrt ASIC reset',
                                                                          0, 65535, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femPpcMode']                   = AttributeContainer(uint32, 'FemPpcMode', 'Fem PPC mode 0=single train shot with PPC reset, 1=Continuous readout',
                                                                          0, 1, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['numberTrains']                 = AttributeContainer(uint32, 'NumberTrains', 'Number of trains [if LL Data Generator or PPC Data Direct selected]',
                                                                          0, 10024, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set, composite")

        self.expectedParameters['tenGigFarmMode']               = AttributeContainer(uint32, 'TenGigFarmMode', '10GigE farm mode 1=Disabled, 2=Fixed IP, multi port, 3=Farm mode with nic lists',
                                                                          1, 3, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femAsicVersion']               = AttributeContainer(uint32, 'FemAsicVersion', 'ASIC Version 1=version 1, 2=version 2',
                                                                          1, 2, 2,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['femAsicClockSource']           = AttributeContainer(uint32, 'FemAsicClockSource', 'ASIC clock source 0=Fem local oscillator (100MHz), 1=XFEL synched clock (99 MHz), 2=PETRAIII synched clock (~114 MHz), 3=Diamond',
                                                                          0, 3, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set, composite")

        self.expectedParameters['femStartTrainSource']          = AttributeContainer(uint32, 'FemStartTrainSource', 'Train start signal source 0=XFEL Clock & Ctrl command/reset, 1=Software, 2=LCLS, 3=Petra (derived from PETRAIII clock), 4=Diamond',
                                                                          0, 4, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set, composite")
                                                                          
        self.expectedParameters['femStartTrainDelay']           = AttributeContainer(uint32, 'FemStartTrainDelay', 'Delay between trigger arrival and start of train (in FEM clock cycles)',
                                                                          0, 4294967295, 100,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set, composite")

        self.expectedParameters['femStartTrainInhibit']         = AttributeContainer(uint32, 'FemStartTrainInhibit', 'Inhibit period after each trigger (in FEM clock cycles) which holds off further triggers to allow data to be readout',
                                                                          0, 4294967295, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femAsicGainOverride']          = AttributeContainer(bool, 'FemAsicGainOverride', 'Enable Fem gain selection override False=Gain set by femAsicGain, True=Gain set by Asic Command Sequence XML tag(s)',
                                                                          (True, False), None, False,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femDebugLevel']                = AttributeContainer(uint32, 'FemDebugLevel', 'Set the debug level',
                                                                          0, 6, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['tenGig0DataGenerator']         = AttributeContainer(uint32, 'TenGig0DataGenerator', '10GigE 0 Data generator 1=Data Generator 2=PPC DDR2; Only relevant if femDataSource=2 [Frame Generator]',
                                                                          1, 2, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['tenGig0DataFormat']            = AttributeContainer(uint32, 'TenGig0DataFormat', '10GigE 0 Data format type 0=counting data; Only relevant if femDataSource=2 [Frame Generator]',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['tenGig0FrameLength']           = AttributeContainer(uint32, 'TenGig0FrameLength', '10GigE 0 Frame length in bytes; Only relevant if femDataSource=2 [Frame Generator]',
                                                                          0, 0xFFFFFF, 0x10000,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['tenGig0NumberOfFrames']        = AttributeContainer(uint32, 'TenGig0NumberOfFrames', '10GigE 0 Number of frames to send in each cycle; Only relevant if femDataSource=2 [Frame Generator]',
                                                                          0, 512, 1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femStartTrainPolarity']        = AttributeContainer(uint32, 'FemStartTrainPolarity', 'Set polarity of the external signal indicating start of train 0=No inversion, 1=Invert signal',
                                                                          (0, 1), None, True,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femVetoPolarity']              = AttributeContainer(uint32, 'FemVetoPolarity', 'Set polarity of the external veto signal 0=No inversion, 1=Invert signal',
                                                                          (0, 1), None, True,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femModuleId']                  = AttributeContainer([uint32]*16, 'FemModuleId', 'ID for FEM to differentiate from which FEM data is coming from',
                                                                          0, 4294967295, [0]*16,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        # 
        # Clock & Control Card Variables - To Assist Integration of C&C into FEM
        #

        self.expectedParameters['cccSystemMode']                  = AttributeContainer(uint32, 'cccSystemMode', 'Clock & Control System Mode 0=Without C&C, 1=C&C without vetoes, 2=With C&C and vetoes',
                                                                          0, 2,  0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['cccEmulationMode']               = AttributeContainer(bool, 'cccEmulationMode', 'Enable to emulate Clock & Control commands (for testing in absence of C&C)',
                                                                          (True, False), None, False,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['cccProvideNumberImages']         = AttributeContainer(bool, 'cccProvideNumberImages', 'ASICs will send "numberImages" images (BUT only if cccSystemMode=2) True=C&C decides, False=Use numberImages',
                                                                          (True, False), None, True,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['cccVetoStartDelay']              = AttributeContainer(uint32, 'cccVetoStartDelay', 'Adjust timing of veto arrival (in steps of clock cycles)',
                                                                          0, 4294967295,  0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['cccStopDelay']                   = AttributeContainer(uint32, 'cccStopDelay', 'Adjust timing of the stop (in steps of clock cycles)',
                                                                          0, 4294967295,  0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['cccResetDelay']                  = AttributeContainer(uint32, 'cccResetDelay', 'Adjust timing of reset (in steps of clock cycles)',
                                                                          0, 4294967295,  0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['cccVetoPatternFile']             = AttributeContainer(str, 'cccVetoPatternFile', 'Filename containing the veto bunch pattern (10 patterns, 3072 bits each)',
                                                                          None, None, 'vetoBunchPattern.xml',
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['cccEmulatorFixedRateStarts']            = AttributeContainer(bool, 'cccEmulatorFixedRateStarts', 'Enables fixed rate train triggers, only used if running with cccEmulationMode = True',
                                                                          (True, False), None, False,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['trainGenInterval']     = AttributeContainer(uint32, 'trainGenInterval', 'Interval (in 100 mhz clock periods) between internally generated Train start commands',
                                                                          0, 4294967295, 10000000,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
                                        
        self.expectedParameters['femAsicTestDataPatternType']            = AttributeContainer(uint32, 'FemAsicTestDataPatternType', 'Increment test data option [if femAsicDataType=1] 0=Every Pixel 1=Only Every Image',
                                                                          0, 1, 0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['femPpcEmulatePipeline']                 = AttributeContainer(bool, 'femPpcEmulatePipeline', 'Emulate Pipeline to compute the Pulse Number and Cell ID for the Image Descriptors',
                                                                          (True, False), None, True,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femPpcImageReordering']                 = AttributeContainer(bool, 'femPpcImageReordering', 'Enable reordering images in readout by Pulse Number if femPpcEmulatePipeline enabled',
                                                                          (True, False), None, True,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femLpdClientVersion']                   = AttributeContainer(uint32, 'FemLpdClientVersion', ' LpdFemClient Software Version - Read Only',
                                                                          0, 4294967295, 0x10000004,
                                                                          AccessRead, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['femTrainIdInitLsw']                     = AttributeContainer(uint32, 'FemTrainIdInitLsw', 'Train ID initial (lower 32-bit) value, Not applicable for C&C nor Data Checker',
                                                                          0, 4294967295,  1,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")
        
        self.expectedParameters['femTrainIdInitMsw']                     = AttributeContainer(uint32, 'FemTrainIdInitMsw', 'Train ID initial (upper 32-bit) value, Not applicable for C&C nor Data Checker',
                                                                          0, 4294967295,  0,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['timeoutTrain']                          = AttributeContainer(uint32, 'timeoutTrain', 'Timeout in seconds on waiting for next Train during run',
                                                                          0, 4294967295,  10,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        self.expectedParameters['numPulsesInTrainOverride']                     = AttributeContainer(uint32, 'numPulsesInTrainOverride', 'Length of XRay Pulse Train (number pulses)',
                                                                          0, 4294967295,  1536,
                                                                          AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")

        #self.expectedParameters['pipelineLatency']                     = AttributeContainer(uint32, 'pipelineLatency', 'Latency of Asic pipeline. Separation in number of pulses between pipeline write and trigger pointers ;  NB Must be set by user to match contents of asic command file. Min = 2. Max = 511.',
                                                                          #0, 511, 2,
                                                                          #AccessWrite, AssignmentOptional, ExternalParam, 'AllOk.Idle', "once, set")


        # 
        # Firmware version variables - used to obtain read only, firmware version numbers
        #

        self.expectedParameters['femV5FirmwareVersion']         = AttributeContainer(uint32, 'FemV5FirmwareVersion', 'FEM V5 Firmware Version',
                                                                          0, 4294967295,  None,
                                                                          AccessRead, None, ExternalParam, 'AllOk.Idle', "once", None, None)

        self.expectedParameters['femBotSp3FirmwareVersion']     = AttributeContainer(uint32, 'FemBotSp3FirmwareVersion', 'FEM Bottom SP3 FPGA Firmware Version',
                                                                          0, 4294967295,  None,
                                                                          AccessRead, None, ExternalParam, 'AllOk.Idle', "once", None, None)

        self.expectedParameters['femTopSp3FirmwareVersion']     = AttributeContainer(uint32, 'FemTopSp3FirmwareVersion', 'FEM Top SP3 FPGA Firmware Version',
                                                                          0, 4294967295,  None,
                                                                          AccessRead, None, ExternalParam, 'AllOk.Idle', "once", None, None)

        self.expectedParameters['femCfgSp3FirmwareVersion']     = AttributeContainer(uint32, 'FemCfgSp3FirmwareVersion', 'FEM Config SP3 FPGA Firmware Version',
                                                                          0, 4294967295,  None,
                                                                          AccessRead, None, ExternalParam, 'AllOk.Idle', "once", None, None)
    
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
            
            if attrib.tags != None:
                templateStr += 'e.tags(\"%s\")\n' % (attrib.tags)
                
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
