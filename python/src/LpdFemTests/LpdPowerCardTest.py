from LpdDevice.LpdDevice import LpdDevice

def powerCardTest():
    
    theDevice = LpdDevice()

    
    rc = theDevice.open('192.168.2.2', 6969)
    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device: %s" % (theDevice.errorStringGet())
        return
    
    print "Status:"
    print "    Low voltage = ",
    (rc, bLowVoltageOff) = theDevice.paramGet('asicPowerEnable')
    if rc != LpdDevice.ERROR_OK:
        print "asicPowerEnable get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else: 
        if bLowVoltageOff:
            print "off."
        else:
            print "on."
        
    print "    High voltage = ",
    (rc, bHighVoltageOff) = theDevice.paramGet('sensorBiasEnable')
    if rc != LpdDevice.ERROR_OK:
        print "sensorBiasEnable get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else: 
        if bHighVoltageOff:
            print "off."
        else:
            print "on."
        
    print "    HV setting: ",
    (rc, hvBias) = theDevice.paramGet('sensorBias')
    if rc != LpdDevice.ERROR_OK:
        print "sensorBias get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print hvBias


    print "Flags:" 
    print "    Fault Flag        = ",  
    (rc, sFaultStatus) = theDevice.paramGet('powerCardFault')
    if rc != LpdDevice.ERROR_OK:
        print "powerCardFaultStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print sFaultStatus

    print "    Fem Status   Trip = ", 
    (rc, sFemStatus) = theDevice.paramGet('powerCardFemStatus')
    if rc != LpdDevice.ERROR_OK:
        print "powerCardFemStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print sFemStatus
        
    print "    External     Trip = ",
    (rc, sExtStatus) = theDevice.paramGet('powerCardExtStatus')
    if rc != LpdDevice.ERROR_OK:
        print "powerCardExtStatus get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print sExtStatus
        
    print "    Over current Trip = ",
    (rc, sOverCurrentStatus) = theDevice.paramGet('powerCardOverCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "powerCardOverCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print sOverCurrentStatus
        
    print "    Over temp    Trip = ",
    (rc, sOvertempStatus) = theDevice.paramGet('powerCardOverTemp')
    if rc != LpdDevice.ERROR_OK:
        print "powerCardOverTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print sOvertempStatus

    print "    Undertemp    Trip = ",
    (rc, sUndertempStatus) = theDevice.paramGet('powerCardUnderTemp')
    if rc != LpdDevice.ERROR_OK:
        print "powerCardUnderTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print sUndertempStatus

    print ".\n"



    print "Temperature readings:"

    (rc, theTemp) = theDevice.paramGet('powerCardTemp')
    if rc != LpdDevice.ERROR_OK:
        print "powerCardTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   PSU Card Temp: %.2f' % theTemp, '  V'

    (rc, theTemp) = theDevice.paramGet('sensorATemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorATemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor A Temp: %.2f' % theTemp, '  V'    # rc =', rc

    (rc, theTemp) = theDevice.paramGet('sensorBTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorBTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor B Temp: %.2f' % theTemp, '  V'    # rc =', rc
        
    (rc, theTemp) = theDevice.paramGet('sensorCTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorCTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor C Temp: %.2f' % theTemp, '  V'    # rc =', rc
        
    (rc, theTemp) = theDevice.paramGet('sensorDTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorDTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor D Temp: %.2f' % theTemp, '  V'    # rc =', rc
        
    (rc, theTemp) = theDevice.paramGet('sensorETemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorETemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor E Temp: %.2f' % theTemp, '  V'    # rc =', rc
        
    (rc, theTemp) = theDevice.paramGet('sensorFTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorFTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor F Temp: %.2f' % theTemp, '  V'    # rc =', rc
        
    (rc, theTemp) = theDevice.paramGet('sensorGTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorGTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor G Temp: %.2f' % theTemp, '  V'    # rc =', rc
        
    (rc, theTemp) = theDevice.paramGet('sensorHTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorHTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor H Temp: %.2f' % theTemp, '  V'    # rc =', rc
        
    theDevice.close()

if __name__ == '__main__':
    
    powerCardTest()
    