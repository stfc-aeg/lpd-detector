"""
    LpdSuperModulePowerCardTest - Cloned from LpdPowerCardTest and modified to read out both power cards

"""


from LpdDevice.LpdDevice import LpdDevice

def powerCardTest():
    
    theDevice = LpdDevice()
    
    rc = theDevice.open('192.168.2.2', 6969, asicModuleType=0)

    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device: %s" % (theDevice.errorStringGet())
        return
    
    print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
    numSensors = 16
    paramTypes = ['Temp'] # TODO add in voltage and current
    
    results = {}
    
    for sensor in range(numSensors):
        
        for paramType in paramTypes:
            paramName = 'sensor' + str(sensor) + paramType
            
            (rc, val) = theDevice.paramGet(paramName)

            results[paramName] = val
            if rc != LpdDevice.ERROR_OK:    
                print "Unable to read parameter %s rc=%d: %s" % (paramName, rc, theDevice.errorStringGet())
            
         
#    # Read right-hand side Power Card's quantities
#    (rc, bRightLvOff) = theDevice.paramGet('asicPowerEnable')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)asicPowerEnable get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightHvBias) = theDevice.paramGet('sensorBias')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorBias get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, bRightHvOff) = theDevice.paramGet('sensorBiasEnable')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorBiasEnable get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#
#    (rc, sRightFaultStatus) = theDevice.paramGet('powerCardFault')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)powerCardFaultStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, sRightFemStatus) = theDevice.paramGet('powerCardFemStatus')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)powerCardFemStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, sRightExtStatus) = theDevice.paramGet('powerCardExtStatus')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)powerCardExtStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, sRightOverCurrentStatus) = theDevice.paramGet('powerCardOverCurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)powerCardOverCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, sRightOvertempStatus) = theDevice.paramGet('powerCardOverTemp')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)powerCardOverTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, sRightUndertempStatus) = theDevice.paramGet('powerCardUnderTemp')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)powerCardUnderTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#
#    (rc, rightPsuCardTemp) = theDevice.paramGet('powerCardTemp')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)powerCardTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorATemp) = theDevice.paramGet('sensorATemp')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorATemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorBTemp) = theDevice.paramGet('sensorBTemp')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)SensorBTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorCTemp) = theDevice.paramGet('sensorCTemp')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)SensorCTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorDTemp) = theDevice.paramGet('sensorDTemp')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)SensorDTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorETemp) = theDevice.paramGet('sensorETemp')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)SensorETemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorFTemp) = theDevice.paramGet('sensorFTemp')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)SensorFTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorGTemp) = theDevice.paramGet('sensorGTemp')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)SensorGTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorHTemp) = theDevice.paramGet('sensorHTemp')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)SensorHTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#
#    (rc, rightFemVoltage) = theDevice.paramGet('femVoltage')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)femVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightFemCurrent) = theDevice.paramGet('femCurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)femCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightDigitalVoltage) = theDevice.paramGet('digitalVoltage')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)digitalVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightDigitalCurrent) = theDevice.paramGet('digitalCurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)digitalCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorAVoltage) = theDevice.paramGet('sensorAVoltage')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorAVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorACurrent) = theDevice.paramGet('sensorACurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorACurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorBVoltage) = theDevice.paramGet('sensorBVoltage')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorBVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorBCurrent) = theDevice.paramGet('sensorBCurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorBCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorCVoltage) = theDevice.paramGet('sensorCVoltage')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorCVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorCCurrent) = theDevice.paramGet('sensorCCurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorCCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorDVoltage) = theDevice.paramGet('sensorDVoltage')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorDVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorDCurrent) = theDevice.paramGet('sensorDCurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorDCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    
#    (rc, rightSensorEVoltage) = theDevice.paramGet('sensorEVoltage')
#    if rc != LpdDevice.ERROR_OK:
#        print"(RHS)sensorEVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorECurrent) = theDevice.paramGet('sensorECurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print"(RHS)sensorECurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorFVoltage) = theDevice.paramGet('sensorFVoltage')
#    if rc != LpdDevice.ERROR_OK:
#        print"(RHS)sensorFVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorFCurrent) = theDevice.paramGet('sensorFCurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print"(RHS)sensorFCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorGVoltage) = theDevice.paramGet('sensorGVoltage')
#    if rc != LpdDevice.ERROR_OK:
#        print"(RHS)sensorGVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorGCurrent) = theDevice.paramGet('sensorGCurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print"(RHS)sensorGCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorHVoltage) = theDevice.paramGet('sensorHVoltage')
#    if rc != LpdDevice.ERROR_OK:
#        print"(RHS)sensorHVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorHCurrent) = theDevice.paramGet('sensorHCurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print"(RHS)sensorHCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#
#    (rc, rightSensorBiasVoltage) = theDevice.paramGet('sensorBiasVoltage')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorBiasVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#    (rc, rightSensorBiasCurrent) = theDevice.paramGet('sensorBiasCurrent')
#    if rc != LpdDevice.ERROR_OK:
#        print "(RHS)sensorBiasCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
#
#    # --------------------------------------------------------------- #
#    # --------------------------------------------------------------- #
#
#    print "    ~+~+~+~+~+~+~ RHS ~+~+~+~+~+~+~+~+~ LHS ~+~+~+~+~+~+~"
#    
#    print "Status:"
#    print "    Low voltage  = ",
#    if bRightLvOff[0]:
#        print "off.",
#    else:
#        print "on.",
#    print "\t    Low voltage  = ",
#    if bRightLvOff[1]:
#        print "off."
#    else:
#        print "on."
#        
#    print "    High voltage = ",
#    if bRightHvOff[0]:
#        print "off.",
#    else:
#        print "on.",
#    print "\t    High voltage = ",
#    if bRightHvOff[1]:
#        print "off."
#    else:
#        print "on."
#        
#    print "    HV setting: ", rightHvBias[0] , "V", "\t    HV setting: ", rightHvBias[1], "V"
#
#    print "Flags:" 
#    print "    Fault Flag        = ", sRightFaultStatus[0], "\t    Fault Flag        = ", sRightFaultStatus[1]
#    print "    Fem Status   Trip = ", sRightFemStatus[0], "\t    Fem Status   Trip = ", sRightFemStatus[1]
#    print "    External     Trip = ", sRightExtStatus[0], "\t    External     Trip = ", sRightExtStatus[1]
#    print "    Over current Trip = ", sRightOverCurrentStatus[0], "\t    Over current Trip = ", sRightOverCurrentStatus[1]
#    print "    Over temp    Trip = ", sRightOvertempStatus[0], "\t    Over temp    Trip = ", sRightOvertempStatus[1]
#    print "    Undertemp    Trip = ", sRightUndertempStatus[0], "\t    Undertemp    Trip = ", sRightUndertempStatus[1], ".\n"
#
#    # Display temperature readings from PSU Card and Sensors
    print "Temperature readings:"
#    print '   PSU Card Temp: %.2f' % rightPsuCardTemp[0], '  C',
#    print '\t   PSU Card Temp: %.2f' % rightPsuCardTemp[1], '  C'

    print '   Sensor  8 Temp: %5.2f' %  results['sensor8Temp'], '  C', '\t   Sensor 0 Temp: %5.2f' % results['sensor0Temp'], '  C'
    print '   Sensor  9 Temp: %5.2f' %  results['sensor9Temp'], '  C', '\t   Sensor 1 Temp: %5.2f' % results['sensor1Temp'], '  C'
    print '   Sensor 10 Temp: %5.2f' % results['sensor10Temp'], '  C', '\t   Sensor 2 Temp: %5.2f' % results['sensor2Temp'], '  C'
    print '   Sensor 11 Temp: %5.2f' % results['sensor11Temp'], '  C', '\t   Sensor 3 Temp: %5.2f' % results['sensor3Temp'], '  C'
    print '   Sensor 12 Temp: %5.2f' % results['sensor12Temp'], '  C', '\t   Sensor 4 Temp: %5.2f' % results['sensor4Temp'], '  C'
    print '   Sensor 13 Temp: %5.2f' % results['sensor13Temp'], '  C', '\t   Sensor 5 Temp: %5.2f' % results['sensor5Temp'], '  C'
    print '   Sensor 14 Temp: %5.2f' % results['sensor14Temp'], '  C', '\t   Sensor 6 Temp: %5.2f' % results['sensor6Temp'], '  C'
    print '   Sensor 15 Temp: %5.2f' % results['sensor15Temp'], '  C', '\t   Sensor 7 Temp: %5.2f' % results['sensor7Temp'], '  C'
#
#    # Display Fem, Digital, sensors voltages and current
#    print "\nOutputs: "
#
#    print "   V FEM      : %.2f" % rightFemVoltage[0], " V ", "%.2f" % rightFemCurrent[0], " A",
#    print "\t   V FEM      : %.2f" % rightFemVoltage[1], " V ", "%.2f" % rightFemCurrent[1], " A"
#    print "   V Digital  : %.2f" % rightDigitalVoltage[0], " V ", "%.2f" % rightDigitalCurrent[0], " mA",
#    print "\t   V Digital  : %.2f" % rightDigitalVoltage[1], " V ", "%.2f" % rightDigitalCurrent[1], " mA\n"
#
#    print "   V Sensor H : %.2f" % rightSensorHVoltage[0], " V ", "%.2f" % rightSensorHCurrent[0], " A",
#    print "\t   V Sensor A : %.2f" % rightSensorAVoltage[1], " V ", "%.2f" % rightSensorACurrent[1], " A"
#    print "   V Sensor G : %.2f" % rightSensorGVoltage[0], " V ", "%.2f" % rightSensorGCurrent[0], " A",
#    print "\t   V Sensor B : %.2f" % rightSensorBVoltage[1], " V ", "%.2f" % rightSensorBCurrent[1], " A"
#    print "   V Sensor F : %.2f" % rightSensorFVoltage[0], " V ", "%.2f" % rightSensorFCurrent[0], " A",
#    print "\t   V Sensor C : %.2f" % rightSensorCVoltage[1], " V ", "%.2f" % rightSensorCCurrent[1], " A"
#    print "   V Sensor E : %.2f" % rightSensorEVoltage[0], " V ", "%.2f" % rightSensorECurrent[0], " A",
#    print "\t   V Sensor D : %.2f" % rightSensorDVoltage[1], " V ", "%.2f" % rightSensorDCurrent[1], " A"
#    print "   V Sensor D : %.2f" % rightSensorDVoltage[0], " V ", "%.2f" % rightSensorDCurrent[0], " A",
#    print "\t   V Sensor E : %.2f" % rightSensorEVoltage[1], " V ", "%.2f" % rightSensorECurrent[1], " A"
#    print "   V Sensor C : %.2f" % rightSensorCVoltage[0], " V ", "%.2f" % rightSensorCCurrent[0], " A",
#    print "\t   V Sensor F : %.2f" % rightSensorFVoltage[1], " V ", "%.2f" % rightSensorFCurrent[1], " A"
#    print "   V Sensor B : %.2f" % rightSensorBVoltage[0], " V ", "%.2f" %  rightSensorBCurrent[0], " A",
#    print "\t   V Sensor G : %.2f" % rightSensorGVoltage[1], " V ", "%.2f" % rightSensorGCurrent[1], " A"
#    print "   V Sensor A : %.2f" % rightSensorAVoltage[0], " V ", "%.2f" % rightSensorACurrent[0], " A",
#    print "\t   V Sensor H : %.2f" % rightSensorHVoltage[1], " V ", "%.2f" % rightSensorHCurrent[1], " A\n"
#
#    print "   HV Bias    : %.2f" % rightSensorBiasVoltage[0], " V ",
#    print "%.2f" % rightSensorBiasCurrent[0], " uA",
#    print "\t   HV Bias    : %.2f" % rightSensorBiasVoltage[1], " V ",
#    print "%.2f" % rightSensorBiasCurrent[1], " uA"
#
#    print "-- -- -- -- -- -- -- -- --"

    print "Closing Fem connection.. "        
    theDevice.close()

if __name__ == '__main__':
        
    powerCardTest()
    
