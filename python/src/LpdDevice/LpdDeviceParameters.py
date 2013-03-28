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
        
        self.expectedParameters['sensorBias0']           = AttributeContainer(float, 'SensorBias0', 'Sensor 0 HV Bias Voltage [V]',
                                                                        0, 500, 0,
                                                                        AccessWrite, True, ExternalParam, 
                                                                        'AllOk.Idle', 'volt', 'V' )
        
        self.expectedParameters['sensorBias1']           = AttributeContainer(float, 'SensorBias1', 'Sensor 1 HV Bias Voltage [V]',
                                                                        0, 500, 0,
                                                                        AccessWrite, True, ExternalParam, 
                                                                        'AllOk.Idle', 'volt', 'V' )
        
        self.expectedParameters['sensorBiasEnable0']     = AttributeContainer(bool, 'SensorBiasEnable0', 'Sensor 0 HV Bias Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional, ExternalParam,
                                                                        'AllOk.Idle')
        
        self.expectedParameters['sensorBiasEnable1']     = AttributeContainer(bool, 'SensorBiasEnable1', 'Sensor 1 HV Bias Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional, ExternalParam,
                                                                        'AllOk.Idle')
        
        self.expectedParameters['asicPowerEnable0']      = AttributeContainer(bool, 'AsicPowerEnable0', 'ASIC 0 LV Power Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional, ExternalParam,
                                                                        'AllOk.Idle')

        self.expectedParameters['asicPowerEnable1']      = AttributeContainer(bool, 'AsicPowerEnable1', 'ASIC 1 LV Power Enable',
                                                                        (True, False), None, False,
                                                                        AccessWrite, AssignmentOptional, ExternalParam,
                                                                        'AllOk.Idle')
            
        #
        # Power card monitoring parameters
        #
        
        self.expectedParameters['powerCardFault0']       = AttributeContainer(bool, 'PowerCardFault0', 'Power Card 0 Fault Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardFault1']       = AttributeContainer(bool, 'PowerCardFault1', 'Power Card 1 Fault Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardFemStatus0']   = AttributeContainer(bool, 'PowerCardFemStatus0', 'Power Card 0 FEM Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardFemStatus1']   = AttributeContainer(bool, 'PowerCardFemStatus1', 'Power Card 1 FEM Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardExtStatus0']   = AttributeContainer(bool, 'PowerCardExtStatus0', 'Power Card 0 External Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardExtStatus1']   = AttributeContainer(bool, 'PowerCardExtStatus1', 'Power Card 1 External Status Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardOverCurrent0'] = AttributeContainer(bool, 'PowerCardOverCurrent0', 'Power Card 0 Overcurrent Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardOverCurrent1'] = AttributeContainer(bool, 'PowerCardOverCurrent1', 'Power Card 1 Overcurrent Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardOverTemp0']    = AttributeContainer(bool, 'PowerCardOverTemp0', 'Power Card Over 0 Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardOverTemp1']    = AttributeContainer(bool, 'PowerCardOverTemp0', 'Power Card Over 1 Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardUnderTemp0']   = AttributeContainer(bool, 'PowerCardUnderTemp0', 'Power Card Under 0 Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardUnderTemp1']   = AttributeContainer(bool, 'PowerCardUnderTemp1', 'Power Card Under 1 Temperature Flag',
                                                                        (True, False), None, None,
                                                                        AccessRead, None, ExternalParam, None)
        
        self.expectedParameters['powerCardTemp0']        = AttributeContainer(float, 'PowerCardTemp0', 'Power Card 0 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['powerCardTemp1']        = AttributeContainer(float, 'PowerCardTemp', 'Power Card 1 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor0Temp']          = AttributeContainer(float, 'Sensor0Temp', 'Sensor 0 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor1Temp']          = AttributeContainer(float, 'Sensor1Temp', 'Sensor 1 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
                            
        self.expectedParameters['sensor2Temp']          = AttributeContainer(float, 'Sensor2Temp', 'Sensor 2 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor3Temp']          = AttributeContainer(float, 'Sensor3Temp', 'Sensor 3 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor4Temp']          = AttributeContainer(float, 'Sensor4Temp', 'Sensor 4 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor5Temp']          = AttributeContainer(float, 'Sensor5Temp', 'Sensor 5 Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor6Temp']          = AttributeContainer(float, 'Sensor6Temp', 'Sensor 6 Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor7Temp']          = AttributeContainer(float, 'Sensor7Temp', 'Sensor 7 Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor8Temp']          = AttributeContainer(float, 'Sensor8Temp', 'Sensor 8 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor9Temp']          = AttributeContainer(float, 'Sensor9Temp', 'Sensor 9 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
                            
        self.expectedParameters['sensor10Temp']          = AttributeContainer(float, 'Sensor10Temp', 'Sensor 10 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor11Temp']          = AttributeContainer(float, 'Sensor11Temp', 'Sensor 11 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor12Temp']          = AttributeContainer(float, 'Sensor12Temp', 'Sensor 12 Temperature [C]',
                                                                        0, 100,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor13Temp']          = AttributeContainer(float, 'Sensor13Temp', 'Sensor 13 Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor14Temp']          = AttributeContainer(float, 'Sensor14Temp', 'Sensor 14 Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['sensor15Temp']          = AttributeContainer(float, 'Sensor15Temp', 'Sensor 15 Temperature [C]',
                                                                      0, 100,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Celsius', 'C')
        
        self.expectedParameters['femVoltage0']           = AttributeContainer(float, 'FemVoltage0', 'FEM 5V Supply 0 Voltage [V]',
                                                                      0, 6,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['femVoltage1']           = AttributeContainer(float, 'FemVoltage1', 'FEM 5V Supply 1 Voltage [V]',
                                                                      0, 6,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['femCurrent0']           = AttributeContainer(float, 'FemCurrent0', 'FEM 5V Supply 0 Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['femCurrent1']           = AttributeContainer(float, 'FemCurrent1', 'FEM 5V Supply 1 Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['digitalVoltage0']       = AttributeContainer(float, 'DigitalVoltage0', 'ASIC 1.2V Digital Supply 0 Voltage [V]',
                                                                      0, 2,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['digitalVoltage1']       = AttributeContainer(float, 'DigitalVoltage1', 'ASIC 1.2V Digital Supply 1 Voltage [V]',
                                                                      0, 2,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')

        self.expectedParameters['digitalCurrent0']       = AttributeContainer(float, 'DigitalCurrent0', 'ASIC 1.2V Digital Supply 0 Current [mA]',
                                                                      0, 1000,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Milliamps', 'mA')
        
        self.expectedParameters['digitalCurrent1']       = AttributeContainer(float, 'DigitalCurrent1', 'ASIC 1.2V Digital Supply 1 Current [mA]',
                                                                      0, 1000,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Milliamps', 'mA')
        
        self.expectedParameters['sensor0Voltage']          = AttributeContainer(float, 'Sensor0Voltage', 'Sensor 0 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor1Voltage']          = AttributeContainer(float, 'Sensor1Voltage', 'Sensor 1 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Volts', 'V')
                            
        self.expectedParameters['sensor2Voltage']          = AttributeContainer(float, 'Sensor2Voltage', 'Sensor 2 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor3Voltage']          = AttributeContainer(float, 'Sensor3Voltage', 'Sensor 3 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor4Voltage']          = AttributeContainer(float, 'Sensor4Voltage', 'Sensor 4 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor5Voltage']          = AttributeContainer(float, 'Sensor5Voltage', 'Sensor 5 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor6Voltage']          = AttributeContainer(float, 'Sensor6Voltage', 'Sensor 6 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor7Voltage']          = AttributeContainer(float, 'Sensor7Voltage', 'Sensor 7 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor8Voltage']          = AttributeContainer(float, 'Sensor8Voltage', 'Sensor 8 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor9Voltage']          = AttributeContainer(float, 'Sensor9Voltage', 'Sensor 9 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Volts', 'V')
                            
        self.expectedParameters['sensor10Voltage']          = AttributeContainer(float, 'Sensor10Voltage', 'Sensor 10 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor11Voltage']          = AttributeContainer(float, 'Sensor11Voltage', 'Sensor 11 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor12Voltage']          = AttributeContainer(float, 'Sensor12Voltage', 'Sensor 12 2.5V Supply Voltage [V]',
                                                                        0, 3,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor13Voltage']          = AttributeContainer(float, 'Sensor13Voltage', 'Sensor 13 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor14Voltage']          = AttributeContainer(float, 'Sensor14Voltage', 'Sensor 14 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor15Voltage']          = AttributeContainer(float, 'Sensor15Voltage', 'Sensor 15 2.5V Supply Voltage [V]',
                                                                      0, 3,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensor0Current']          = AttributeContainer(float, 'Sensor0Current', 'Sensor 0 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor1Current']          = AttributeContainer(float, 'Sensor1Current', 'Sensor 1 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Amps', 'A')
                            
        self.expectedParameters['sensor2Current']          = AttributeContainer(float, 'Sensor2Current', 'Sensor 2 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor3Current']          = AttributeContainer(float, 'Sensor3Current', 'Sensor 3 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor4Current']          = AttributeContainer(float, 'Sensor4Current', 'Sensor 4 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor5Current']          = AttributeContainer(float, 'Sensor5Current', 'Sensor 5 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor6Current']          = AttributeContainer(float, 'Sensor6Current', 'Sensor 6 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor7Current']          = AttributeContainer(float, 'Sensor7Current', 'Sensor 7 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor8Current']          = AttributeContainer(float, 'Sensor8Current', 'Sensor 8 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor9Current']          = AttributeContainer(float, 'Sensor9Current', 'Sensor 9 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Amps', 'A')
                            
        self.expectedParameters['sensor10Current']          = AttributeContainer(float, 'Sensor10Current', 'Sensor 10 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor11Current']          = AttributeContainer(float, 'Sensor11Current', 'Sensor 11 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor12Current']          = AttributeContainer(float, 'Sensor12Current', 'Sensor 12 2.5V Supply Current [A]',
                                                                        0, 10,  None,
                                                                        AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor13Current']          = AttributeContainer(float, 'Sensor13Current', 'Sensor 13 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor14Current']          = AttributeContainer(float, 'Sensor14Current', 'Sensor 14 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensor15Current']          = AttributeContainer(float, 'Sensor15Current', 'Sensor 15 2.5V Supply Current [A]',
                                                                      0, 10,  None,
                                                                      AccessRead, None, ExternalParam, None, 'Amps', 'A')
        
        self.expectedParameters['sensorBiasVoltage0']    = AttributeContainer(float, 'SensorBiasVoltage0', 'Sensor bias 0 voltage readback [V]',
                                                                      0, 600, None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensorBiasVoltage1']    = AttributeContainer(float, 'SensorBiasVoltage1', 'Sensor bias 1 voltage readback [V]',
                                                                      0, 600, None,
                                                                      AccessRead, None, ExternalParam, None, 'Volts', 'V')
        
        self.expectedParameters['sensorBiasCurrent0']    = AttributeContainer(float, 'SensorBiasVoltage0', 'Sensor bias 0 current readback [uA]',
                                                                      0, 600, None,
                                                                      AccessRead, None, ExternalParam, None, 'Microamps', 'uA')

        self.expectedParameters['sensorBiasCurrent1']    = AttributeContainer(float, 'SensorBiasVoltage1', 'Sensor bias 1 current readback [uA]',
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
