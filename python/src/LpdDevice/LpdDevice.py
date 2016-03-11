'''
LpdDevice - XFEL LPD device API class

Created on 18 Sep 2012

@author: Tim Nicholls, STFC Application Engineering Group
'''

from __future__ import print_function, absolute_import

from LpdFemClient.LpdFemClient import LpdFemClient, FemClientError
from LpdDevice.LpdDeviceParameters import *
import time

class LpdDevice(object):
    '''
    This class provides an application programming interface (API) to the LPD
    device, abstracting the details of the underlying FEM client transactions. 
    It implements simple commands (open, close, configure etc) to control the
    state of the LPD FEM, and provides parameter set/get methods for setting
    and retrieving parameters from the device.
    '''
    
    # FemClient connection default timeout
    defaultTimeout = 5
    
    # Error codes returned by this class.
    ERROR_OK                   = 0
    ERROR_FEM_CONNECT_FAILED   = 1000
    ERROR_FEM_CLIENT_EXCEPTION = 1001
    ERROR_PARAM_UNKNOWN        = 2000
    ERROR_PARAM_ILLEGAL_TYPE   = 2001
    ERROR_PARAM_ILLEGAL_VALUE  = 2002
    ERROR_PARAM_UNSET          = 2003
    ERROR_PARAM_VECTOR_LENGTH  = 2004
    ERROR_PARAM_NO_METHOD      = 2005
    ERROR_PARAM_SET_FAILED     = 2006
    ERROR_PARAM_GET_FAILED     = 2007

    def __init__(self, simulateFemClient=False):
        '''
        Constructor for LpdDevice
        
        @param simulateFemClient simulate FEM client connection by storing parameters locally and making dummy command calls
        '''
        
        self.simulateFemClient = simulateFemClient
        
        self.femClient = None
        self.errorString = ''
        
        # expectedParams is a dictionary of expected parameters, with a camelCase key and data in the form of
        # a tuple that specifies everything in Sergei's 'Karabo Parameter Templates' document, namely:
        #
        # 'key' : ( type, displayed name, description, minimum possible value (or tuple of allowed values),
        #           max possible value (ignored if minimum is a tuple of possibles), default value,
        #           access type, assignment policy (True if optional, otherwise mandatory), internal param (true if internal)
        #           unit name, unit symbol )
        self.expectedParams = LpdDeviceParameters().get()
        
        # Generate attributes containing default value for the internal parameters
        for param, attrib in self.expectedParams.items():
            if attrib.isInternal:
                setattr(self, param, attrib.defaultValue)
        
        self.opened = False
    
    def errorStringGet(self):
        '''
        Returns the last error string generated by the class
        '''
        return repr(self.errorString)
    
    def open(self, host, port, timeout=defaultTimeout, asicModuleType=0, legacyPowerCard=False):
        '''
        Opens a client connection to the LPD front-end module (FEM).
        
        @param host IP address of FEM as dotted quad format string
        @param port port of FEM to connect to (integer) 
        @param (optional) client timeout in seconds
        @param (optional) asic module type (defaults to 0 = supermodule)
        @return LpdDevice error code, ERROR_OK or ERROR_FEM_CONNECT_FAILED
        '''
        rc = LpdDevice.ERROR_OK
        self.opened = True
        if not self.simulateFemClient:
            try:
                
                self.femClient = LpdFemClient((host, int(port)), timeout, asicModuleType, legacyPowerCard)

            except FemClientError as e:
                
                self.errorString = e.msg
                rc = LpdDevice.ERROR_FEM_CONNECT_FAILED
                self.opened = False
        else:
            pass
        return rc
    
    def close(self):
        '''
        Closes the client connection to the FEM. All subsequent transactions to
        the device will fail until open() is called again.
        
        @return LpdDevice error code, ERROR_OK or other error condition
        '''
        if self.femClient:
            self.femClient.close()
            self.femClient = None
        self.opened = False
        return LpdDevice.ERROR_OK
    
    def isOpen(self):
        '''
        Check if a connnection to LPD device is open
        @return boolean value
        '''
        return self.opened
    
    def configure(self):
        '''
        Commands the API to upload parameters to the FEM and ASICS and configure
        the system for running.
        
        @return LpdDevice error code, ERROR_OK or other error condition

        '''
        rc = LpdDevice.ERROR_OK
        
        if not self.simulateFemClient:
            try:
                self.femClient.configure()
            except FemClientError as e:
                rc = LpdDevice.ERROR_FEM_CLIENT_EXCEPTION
                self.errorString = 'Error during FEM configuration: %s' % e.msg
                
        else:
            time.sleep(5)
        
        return rc
    
    def start(self, no_wait=False):
        '''
        Starts an acquisition sequence - prepares the FEM and ASICs to receive
        triggers and read out

        @param no_wait - signal to FEM client to not wait for run to complete
        @return LpdDevice error code, ERROR_OK or other error condition
        '''
        
        rc = LpdDevice.ERROR_OK
    
        if not self.simulateFemClient:
            try:
                self.femClient.run(no_wait)
            except FemClientError as e:
                rc = LpdDevice.ERROR_FEM_CLIENT_EXCEPTION
                self.errorString = 'Error during FEM acquisition start: %s' % e.msg
        else:
            pass
                
        return rc
    
    def stop(self):
        '''
        Stops an acquisition sequence - stops readout of the FEM and ASICS. May be called
        once triggers have stopped to cleanly terminate acquisition, or during acquisition
        to abort cleanly

        @return LpdDevice error code, ERROR_OK or other error condition
        '''
        rc = LpdDevice.ERROR_OK
    
        if not self.simulateFemClient:
            try:
                self.femClient.stop()
                pass
            except FemClientError as e:
                rc = LpdDevice.ERROR_FEM_CLIENT_EXCEPTION
                self.errorString = 'Error during FEM acquisition stop: %s' % e.msg
        else:
            pass
                
        return rc
        
    def paramSet(self, param, value, **kwargs):
        '''
        Sets a parameter - sets the parameter specified by name to a given value. This is
        done by resolving the parameter name into a '<paramName>Set' method call in the underlying
        FemClient object. The value is validated for type and length against the allowed 
        parameters. Keyword arguments are accepted to specify ASIC and pixel indices for the
        parameter.
        
        In simulation mode, the parameter value is cached locally in this object to allow it to
        be retrieved by paramGet() calls
        
        @param param - parameter name to be set (string)
        @param value - value (or vector of values) to be set
        @param kwargs - optional keyword argument list
        @return LpdDevice error code, ERROR_OK or other error condition
        '''
        
        rc = LpdDevice.ERROR_OK
        
        # Check if ASIC and/or pixel keyword arguments have been passed. 
        # TODO enforce these for parameters if required, or fall-back to defaults if not?
        if 'asic' in kwargs:
            asic = kwargs['asic']
        else:
            asic = None
        if 'pixel' in kwargs:
            pixel = kwargs['pixel']
        else:
            pixel = None        
        
        # Check if parameter specified is an expected parameter for this device
        if param in self.expectedParams:
            
            # Test if parameter value can be converted to required type, otherwise trap as an illegal
            # value type. Handle vector parameters by converting in a list iterator and check that
            # the correct number of elements are provided
            try:
                if self.expectedParams[param].numElements > 1:
                    
                    # Trap case where vector parameter is expected but only a scalar value received
                    try:
                        valueLen = len(value)
                    except TypeError:
                        rc = LpdDevice.ERROR_PARAM_VECTOR_LENGTH
                        self.errorString = "Got scalar value for vector parameter %s of expected length %d" % \
                            (param, self.expectedParams[param].numElements)
                    else:    
                        if valueLen != self.expectedParams[param].numElements:                        
                            rc = LpdDevice.ERROR_PARAM_VECTOR_LENGTH
                            self.errorString = 'Incorrect length for vector parameter %s specified: expected %d got %d' % \
                                (param, self.expectedParams[param].numElements, len(value))                            
                        else:
                            value = [self.expectedParams[param].type(element) for element in value]
                else:
                    value = self.expectedParams[param].type(value)

            except ValueError:
                rc = LpdDevice.ERROR_PARAM_ILLEGAL_TYPE
                self.errorString = 'Illegal value type for parameter %s specified: expected \'%s\' got \'%s\'' % \
                    (param , self.expectedParams[param].type.__name__, type(value).__name__)

            else:
                
                # Test if value(s) are within legal range. Promote scalar parameter values to a (temporary)
                # list to allow iteration
                if isinstance(value, list):
                    values = value
                else:
                    values = [value]
                    
                for entry in values:
                    
                    # If range was a list of possibilities, test that value exists in range, otherwise test
                    # against minimum and maximum values
                    if self.expectedParams[param].possVals != None:
                        if entry not in self.expectedParams[param].possVals:
                            rc = LpdDevice.ERROR_PARAM_ILLEGAL_VALUE
                            self.errorString = 'Illegal value set %s for parameter %s' % (repr(entry), param)
                            break
                            
                    else:
                        if self.expectedParams[param].minValue != None and entry < self.expectedParams[param].minValue:
                            rc = LpdDevice.ERROR_PARAM_ILLEGAL_VALUE
                            self.errorString = 'Illegal value set %s for parameter %s' % (repr(entry), param)
                            break
                        if self.expectedParams[param].maxValue != None and entry > self.expectedParams[param].maxValue:
                            rc = LpdDevice.ERROR_PARAM_ILLEGAL_VALUE
                            self.errorString = 'Illegal value set %s for parameter %s' % (repr(entry), param)
                            break
                            
                # Only proceed if all values are legal
                if rc == LpdDevice.ERROR_OK:
                            
                    if not self.simulateFemClient:                    
                        
                        # If this is an internal parameter, handle at this level and set a local attribute with the specified value.
                        # Otherwise, resolve the specified FEM client set function with the parameter. Trap the situation where
                        # the appropriate set method is not resolved - shouldn't happen if parameter definitions
                        # match the set/get method implementation
                        
                        if self.expectedParams[param].isInternal:                           
                            setattr(self, param, value)
                            
                        else:
                            
                            try:
                                setMethod  = getattr(self.femClient, '%sSet' % param)
                                
                            except AttributeError:
                                rc = LpdDevice.ERROR_PARAM_NO_METHOD
                                self.errorString = 'Failed to resolve client set method for for parameter %s' % param
                                
                            else:
                                
                                # Call the set method, trapping any FemClient exceptions that are generated 
                                try:
                                    setMethod(value, **kwargs)
                                    
                                except FemClientError as e:
                                    rc = LpdDevice.ERROR_PARAM_SET_FAILED
                                    self.errorString = 'Failed to set parameter %s: %s' % \
                                        (param, e.msg)                        
                    else:                    
                        
                        # In simulation mode, cache the value locally so subsequent gets return the same value
                        paramName = '%s_%s_%s' % (param, asic, pixel)
                        setattr(self, paramName, value)
                    
        else:
            rc = LpdDevice.ERROR_PARAM_UNKNOWN
            self.errorString = 'Attempted to set unknown parameter %s' % (param)
        
        return rc
    
    def paramGet(self, param, **kwargs):
        '''
        Gets a parameter - retrieves the value of a given parameter specified by name in 
        the arguments. This is done by resolving the parameter name into a '<param>Get' call
        to the underlying FemClient object. A return code for the success/failure of the call
        and the value are returned as a tuple to the caller. Keyword arguments are accepted to
        specify the ASIC and pixel if relevant to the parameter.
        
        In simulation mode, the locally-cached value is returned if already set, otherwise an
        error is thrown.
        
        @param param parameter name to get
        @param kwargs optional keyword argument list
        @return LpdDeviceerror code and retrieved value(s) as tuple 
        '''
        
        rc = LpdDevice.ERROR_OK
        value = None
 
        # Check if ASIC and/or pixel keyword arguments have been passed
        if 'asic' in kwargs:
            asic = kwargs['asic']
        else:
            asic = None
        if 'pixel' in kwargs:
            pixel = kwargs['pixel']
        else:
            pixel = None        

        # Check if parameter specified is an expected parameter for this device
        if param in self.expectedParams:
            
            # If not in simulation mode, resolve the getter method in the
            # underlying FemClient object and call it to retrieve the parameter
            if not self.simulateFemClient:

                # If this is an internal parameter, handle at this level and set a local attribute with the specified value

                if self.expectedParams[param].isInternal:
                    try:               
                        value = getattr(self, param)
                
                    except AttributeError:
                        rc = LpdDevice.ERROR_PARAM_UNSET
                        self.errorString = 'Attempt to get unset internal parameter \'%s\'' % param
                
                else:
                    try:
                        getMethod = getattr(self.femClient, '%sGet' % param)
    
                    except AttributeError:
                        rc = LpdDevice.ERROR_PARAM_NO_METHOD
                        self.errorString = "Failed to resolve client get method for parameter %s" % param
    
                    else:
                        
                        # Call the get method, trapping any FemClient exceptions that are generated
                        try:
                            value =  getMethod(**kwargs)
                            
                        except FemClientError as e:
                            rc = LpdDevice.ERROR_PARAM_GET_FAILED
                            self.errorString = 'Failed to get parameter %s: %s' % \
                                (param, e.msg)
                    
            else:
                
                # In simulation mode, resolve the parameter name including pixel and asic 
                # retrieve the locally-cached value
                try:
                    
                    paramName = '%s_%s_%s' % (param, asic, pixel)
                    value = getattr(self, paramName)
                    
                except AttributeError:
                    rc = LpdDevice.ERROR_PARAM_UNSET
                    self.errorString = 'Attempt to get unset parameter \'%s\'' % param
                    
        else:
            rc = LpdDevice.ERROR_PARAM_UNKNOWN
            self.errorString = 'Attempted to get unknown parameter %s' % (param)
            
        return (rc, value)
    
    
if __name__ == '__main__':
    '''
    Test main entry point to illustrate simulated use of LpdDevice API
    '''
    
    # Instantiate the device
    theDevice = LpdDevice(simulateFemClient=True)
    
    # Open client connection to the FEM - IP address and port are ignored in
    # simulation mode
    rc = theDevice.open('127.0.0.1', '6969', timeout=30)
    print('Open device, rc =', rc)
    
    # Set the sensor bias parameter
    sensorBias = 130.3
    rc = theDevice.paramSet('sensorBias', 130.3)
    print('Sensor bias set, rc =', rc)
    
    # Read it back and verify value
    (rc, value) = theDevice.paramGet('sensorBias')
    print('Sensor bias get, rc =', rc, 'value =', value)
    if value != sensorBias:
        print('ERROR, mismatch in sensor bias set and get values')
    
    # Set a pixel and asic specific parameter. ASIC and pixel values are specified by
    # keyword arguments as shown below    
    asic = 37
    pixel = 149
    selfTest = 1
    rc = theDevice.paramSet('femAsicPixelSelfTestOverride', selfTest, asic=asic, pixel=pixel)
    print('Pixel self test override set, rc = ', rc)
    
    # Read the same value back and verify
    (rc, value) = theDevice.paramGet('femAsicPixelSelfTestOverride', asic=asic, pixel=pixel)
    print('Pixel self test override, rc = ', rc, 'value =', value)
    if value != selfTest:
        print("ERROR, mismatch in pixel self-test override set and get values")
     
    # Send a configure command to load parameters into FEM and ASICs    
    rc = theDevice.configure()
    print('Device configure, rc =', rc)
    
    # Start acquisition
    rc = theDevice.start()
    print('Device start, rc =', rc)
    
    # Stop acquisition
    rc = theDevice.stop()
    print('Device stop, rc =', rc)
    
    # Close the client connection
    theDevice.close()
    
