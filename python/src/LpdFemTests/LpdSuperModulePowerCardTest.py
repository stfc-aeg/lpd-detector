"""
    LpdSuperModulePowerCardTest - Cloned from LpdPowerCardTest and modified to read out both power cards

"""


from LpdDevice.LpdDevice import LpdDevice
import sys

def powerCardTest(): #femI2cBus):
    
    theDevice = LpdDevice()

    
    rc = theDevice.open('192.168.2.2', 6969)

    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device: %s" % (theDevice.errorStringGet())
        return
    
    print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"


#            if femI2cBus == 0:
#                femI2cBusName = "LM82"
#            elif femI2cBus == 256:
#                femI2cBusName = "EEPROM"
    femRHSBus = 512
    femLHSBus = 768

    # Connect to left-hand side Power Card
    rc = theDevice.paramSet('femI2cBus', femLHSBus)
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)femI2cBusSet set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        pass

    # Read left-hand side Power Card's quantities
    (rc, bLeftLvOff) = theDevice.paramGet('asicPowerEnable')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)asicPowerEnable get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftHvBias) = theDevice.paramGet('sensorBias')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)sensorBias get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, bLeftHvOff) = theDevice.paramGet('sensorBiasEnable')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)sensorBiasEnable get failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    (rc, sLeftFaultStatus) = theDevice.paramGet('powerCardFault')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)powerCardFaultStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, sLeftFemStatus) = theDevice.paramGet('powerCardFemStatus')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)powerCardFemStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, sLeftExtStatus) = theDevice.paramGet('powerCardExtStatus')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)powerCardExtStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, sLeftOverCurrentStatus) = theDevice.paramGet('powerCardOverCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)powerCardOverCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, sLeftOvertempStatus) = theDevice.paramGet('powerCardOverTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)powerCardOverTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, sLeftUndertempStatus) = theDevice.paramGet('powerCardUnderTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)powerCardUnderTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    (rc, leftPsuCardTemp) = theDevice.paramGet('powerCardTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)powerCardTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorATemp) = theDevice.paramGet('sensorATemp')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)sensorATemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorBTemp) = theDevice.paramGet('sensorBTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)SensorBTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorCTemp) = theDevice.paramGet('sensorCTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)SensorCTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorDTemp) = theDevice.paramGet('sensorDTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)SensorDTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorETemp) = theDevice.paramGet('sensorETemp')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)SensorETemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorFTemp) = theDevice.paramGet('sensorFTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)SensorFTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorGTemp) = theDevice.paramGet('sensorGTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)SensorGTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorHTemp) = theDevice.paramGet('sensorHTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)SensorHTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    (rc, leftFemVoltage) = theDevice.paramGet('femVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)femVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftFemCurrent) = theDevice.paramGet('femCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)femCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftDigitalVoltage) = theDevice.paramGet('digitalVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)digitalVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftDigitalCurrent) = theDevice.paramGet('digitalCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)digitalCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorAVoltage) = theDevice.paramGet('sensorAVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)sensorAVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorACurrent) = theDevice.paramGet('sensorACurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)sensorACurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorBVoltage) = theDevice.paramGet('sensorBVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)sensorBVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorBCurrent) = theDevice.paramGet('sensorBCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)sensorBCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorCVoltage) = theDevice.paramGet('sensorCVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)sensorCVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorCCurrent) = theDevice.paramGet('sensorCCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)sensorCCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorDVoltage) = theDevice.paramGet('sensorDVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)sensorDVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorDCurrent) = theDevice.paramGet('sensorDCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(LHS)sensorDCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    (rc, leftSensorEVoltage) = theDevice.paramGet('sensorEVoltage')
    if rc != LpdDevice.ERROR_OK:
        print"(LHS)sensorEVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorECurrent) = theDevice.paramGet('sensorECurrent')
    if rc != LpdDevice.ERROR_OK:
        print"(LHS)sensorECurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorFVoltage) = theDevice.paramGet('sensorFVoltage')
    if rc != LpdDevice.ERROR_OK:
        print"(LHS)sensorFVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorFCurrent) = theDevice.paramGet('sensorFCurrent')
    if rc != LpdDevice.ERROR_OK:
        print"(LHS)sensorFCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorGVoltage) = theDevice.paramGet('sensorGVoltage')
    if rc != LpdDevice.ERROR_OK:
        print"(LHS)sensorGVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorGCurrent) = theDevice.paramGet('sensorGCurrent')
    if rc != LpdDevice.ERROR_OK:
        print"(LHS)sensorGCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorHVoltage) = theDevice.paramGet('sensorHVoltage')
    if rc != LpdDevice.ERROR_OK:
        print"(LHS)sensorHVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorHCurrent) = theDevice.paramGet('sensorHCurrent')
    if rc != LpdDevice.ERROR_OK:
        print"(LHS)sensorHCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    (rc, leftSensorBiasVoltage) = theDevice.paramGet('sensorBiasVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorBiasVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, leftSensorBiasCurrent) = theDevice.paramGet('sensorBiasCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorBiasCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    # --------------------------------------------------------------- #
    # --------------------------------------------------------------- #

    # Connect to right-hand side Power Card
    rc = theDevice.paramSet('femI2cBus', femRHSBus)
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)femI2cBusSet set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        pass

    # Read right-hand side Power Card's quantities
    (rc, bRightLvOff) = theDevice.paramGet('asicPowerEnable')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)asicPowerEnable get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightHvBias) = theDevice.paramGet('sensorBias')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorBias get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, bRightHvOff) = theDevice.paramGet('sensorBiasEnable')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorBiasEnable get failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    (rc, sRightFaultStatus) = theDevice.paramGet('powerCardFault')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)powerCardFaultStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, sRightFemStatus) = theDevice.paramGet('powerCardFemStatus')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)powerCardFemStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, sRightExtStatus) = theDevice.paramGet('powerCardExtStatus')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)powerCardExtStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, sRightOverCurrentStatus) = theDevice.paramGet('powerCardOverCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)powerCardOverCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, sRightOvertempStatus) = theDevice.paramGet('powerCardOverTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)powerCardOverTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, sRightUndertempStatus) = theDevice.paramGet('powerCardUnderTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)powerCardUnderTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    (rc, rightPsuCardTemp) = theDevice.paramGet('powerCardTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)powerCardTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorATemp) = theDevice.paramGet('sensorATemp')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorATemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorBTemp) = theDevice.paramGet('sensorBTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)SensorBTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorCTemp) = theDevice.paramGet('sensorCTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)SensorCTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorDTemp) = theDevice.paramGet('sensorDTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)SensorDTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorETemp) = theDevice.paramGet('sensorETemp')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)SensorETemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorFTemp) = theDevice.paramGet('sensorFTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)SensorFTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorGTemp) = theDevice.paramGet('sensorGTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)SensorGTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorHTemp) = theDevice.paramGet('sensorHTemp')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)SensorHTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    (rc, rightFemVoltage) = theDevice.paramGet('femVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)femVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightFemCurrent) = theDevice.paramGet('femCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)femCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightDigitalVoltage) = theDevice.paramGet('digitalVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)digitalVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightDigitalCurrent) = theDevice.paramGet('digitalCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)digitalCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorAVoltage) = theDevice.paramGet('sensorAVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorAVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorACurrent) = theDevice.paramGet('sensorACurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorACurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorBVoltage) = theDevice.paramGet('sensorBVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorBVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorBCurrent) = theDevice.paramGet('sensorBCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorBCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorCVoltage) = theDevice.paramGet('sensorCVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorCVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorCCurrent) = theDevice.paramGet('sensorCCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorCCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorDVoltage) = theDevice.paramGet('sensorDVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorDVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorDCurrent) = theDevice.paramGet('sensorDCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorDCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    (rc, rightSensorEVoltage) = theDevice.paramGet('sensorEVoltage')
    if rc != LpdDevice.ERROR_OK:
        print"(RHS)sensorEVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorECurrent) = theDevice.paramGet('sensorECurrent')
    if rc != LpdDevice.ERROR_OK:
        print"(RHS)sensorECurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorFVoltage) = theDevice.paramGet('sensorFVoltage')
    if rc != LpdDevice.ERROR_OK:
        print"(RHS)sensorFVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorFCurrent) = theDevice.paramGet('sensorFCurrent')
    if rc != LpdDevice.ERROR_OK:
        print"(RHS)sensorFCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorGVoltage) = theDevice.paramGet('sensorGVoltage')
    if rc != LpdDevice.ERROR_OK:
        print"(RHS)sensorGVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorGCurrent) = theDevice.paramGet('sensorGCurrent')
    if rc != LpdDevice.ERROR_OK:
        print"(RHS)sensorGCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorHVoltage) = theDevice.paramGet('sensorHVoltage')
    if rc != LpdDevice.ERROR_OK:
        print"(RHS)sensorHVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorHCurrent) = theDevice.paramGet('sensorHCurrent')
    if rc != LpdDevice.ERROR_OK:
        print"(RHS)sensorHCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    (rc, rightSensorBiasVoltage) = theDevice.paramGet('sensorBiasVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorBiasVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    (rc, rightSensorBiasCurrent) = theDevice.paramGet('sensorBiasCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "(RHS)sensorBiasCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())

    # --------------------------------------------------------------- #
    # --------------------------------------------------------------- #

    print "    ~+~+~+~+~+~+~ LHS ~+~+~+~+~+~+~+~+~ RHS ~+~+~+~+~+~+~"
    
    print "Status:"
    print "    Low voltage  = ",
    if bLeftLvOff:
        print "off.",
    else:
        print "on.",
    print "\t    Low voltage  = ",
    if bRightLvOff:
        print "off."
    else:
        print "on."
        
    print "    High voltage = ",
    if bLeftHvOff:
        print "off.",
    else:
        print "on.",
    print "\t    High voltage = ",
    if bRightHvOff:
        print "off."
    else:
        print "on."
        
    print "    HV setting: ",
    print leftHvBias , "V",
    print "\t    HV setting: ",
    print rightHvBias , "V"



    print "Flags:" 
    print "    Fault Flag        = ",  
    print sLeftFaultStatus,
    print "\t    Fault Flag        = ",  
    print sRightFaultStatus

    print "    Fem Status   Trip = ", 
    print sLeftFemStatus,
    print "\t    Fem Status   Trip = ", 
    print sRightFemStatus

    print "    External     Trip = ",
    print sLeftExtStatus,
    print "\t    External     Trip = ",
    print sRightExtStatus
        
    print "    Over current Trip = ",
    print sLeftOverCurrentStatus,
    print "\t    Over current Trip = ",
    print sRightOverCurrentStatus

    print "    Over temp    Trip = ",
    print sLeftOvertempStatus,
    print "\t    Over temp    Trip = ",
    print sRightOvertempStatus

    print "    Undertemp    Trip = ",
    print sLeftUndertempStatus,
    print "\t    Undertemp    Trip = ",
    print sRightUndertempStatus

    print ".\n"

#    # Display temperature readings from PSU Card and Sensors
    print "Temperature readings:"
    print '   PSU Card Temp: %.2f' % leftPsuCardTemp, '  C',
    print '\t   PSU Card Temp: %.2f' % rightPsuCardTemp, '  C'
    print '   Sensor A Temp: %.2f' % leftSensorATemp, '  C',
    print '\t   Sensor A Temp: %.2f' % rightSensorATemp, '  C'
    print '   Sensor B Temp: %.2f' % leftSensorBTemp, '  C',
    print '\t   Sensor B Temp: %.2f' % rightSensorBTemp, '  C'
    print '   Sensor C Temp: %.2f' % leftSensorCTemp, '  C',
    print '\t   Sensor C Temp: %.2f' % rightSensorCTemp, '  C'
    print '   Sensor D Temp: %.2f' % leftSensorDTemp, '  C',
    print '\t   Sensor D Temp: %.2f' % rightSensorDTemp, '  C'
    print '   Sensor E Temp: %.2f' % leftSensorETemp, '  C',
    print '\t   Sensor E Temp: %.2f' % rightSensorETemp, '  C'
    print '   Sensor F Temp: %.2f' % leftSensorFTemp, '  C',
    print '\t   Sensor F Temp: %.2f' % rightSensorFTemp, '  C'
    print '   Sensor G Temp: %.2f' % leftSensorGTemp, '  C',
    print '\t   Sensor G Temp: %.2f' % rightSensorGTemp, '  C'
    print '   Sensor H Temp: %.2f' % leftSensorHTemp, '  C',
    print '\t   Sensor H Temp: %.2f' % rightSensorHTemp, '  C'

    # Display Fem, Digital, sensors voltages and current
    print "\nOutputs: "

    print "   V FEM      : %.2f" % leftFemVoltage, " V ",
    print "%.2f" % leftFemCurrent, " A",
    print "\t   V FEM      : %.2f" % rightFemVoltage, " V ",
    print "%.2f" % rightFemCurrent, " A"
    print "   V Digital  : %.2f" % leftDigitalVoltage, " V ",
    print "%.2f" % leftDigitalCurrent, " mA",
    print "\t   V Digital  : %.2f" % rightDigitalVoltage, " V ",
    print "%.2f" % rightDigitalCurrent, " mA\n"
    print "   V Sensor A : %.2f" % leftSensorAVoltage, " V ",
    print "%.2f" % leftSensorACurrent, " A",
    print "\t   V Sensor A : %.2f" % rightSensorAVoltage, " V ",
    print "%.2f" % rightSensorACurrent, " A"


    print "   V Sensor B : %.2f" % leftSensorBVoltage, " V ",
    print "%.2f" %  leftSensorBCurrent, " A",
    print "\t   V Sensor B : %.2f" % rightSensorBVoltage, " V ",
    print "%.2f" % rightSensorBCurrent, " A"
    print "   V Sensor C : %.2f" % leftSensorCVoltage, " V ",
    print "%.2f" % leftSensorCCurrent, " A",
    print "\t   V Sensor C : %.2f" % rightSensorCVoltage, " V ",
    print "%.2f" % rightSensorCCurrent, " A"
    print "   V Sensor D : %.2f" % leftSensorDVoltage, " V ",
    print "%.2f" % leftSensorDCurrent, " A",
    print "\t   V Sensor D : %.2f" % rightSensorDVoltage, " V ",
    print "%.2f" % rightSensorDCurrent, " A"

    print "   V Sensor E : %.2f" % leftSensorEVoltage, " V ",
    print "%.2f" % leftSensorECurrent, " A",
    print "\t   V Sensor E : %.2f" % rightSensorEVoltage, " V ",
    print "%.2f" % rightSensorECurrent, " A"
    print "   V Sensor F : %.2f" % leftSensorFVoltage, " V ",
    print "%.2f" % leftSensorFCurrent, " A",
    print "\t   V Sensor F : %.2f" % rightSensorFVoltage, " V ",
    print "%.2f" % rightSensorFCurrent, " A"

    print "   V Sensor G : %.2f" % leftSensorGVoltage, " V ",
    print "%.2f" % leftSensorGCurrent, " A",
    print "\t   V Sensor G : %.2f" % rightSensorGVoltage, " V ",
    print "%.2f" % rightSensorGCurrent, " A"
    print "   V Sensor H : %.2f" % leftSensorHVoltage, " V ",
    print "%.2f" % leftSensorHCurrent, " A",
    print "\t   V Sensor H : %.2f" % rightSensorHVoltage, " V ",
    print "%.2f" % rightSensorHCurrent, " A"


    print ""

    


    print "   HV Bias    : %.2f" % leftSensorBiasVoltage, " V ",
    print "%.2f" % leftSensorBiasCurrent, " uA",
    print "\t   HV Bias    : %.2f" % rightSensorBiasVoltage, " V ",
    print "%.2f" % rightSensorBiasCurrent, " uA"
    
    print "-- -- -- -- -- -- -- -- --"

    print "Closing Fem connection.. "        
    theDevice.close()

if __name__ == '__main__':

#    if len(sys.argv) == 2:
#        femI2cBus = int(sys.argv[1], 16)
#    else:
#        femI2cBus = None
        
    powerCardTest() #femI2cBus)
    
