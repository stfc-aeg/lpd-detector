from LpdDevice.LpdDevice import LpdDevice
import sys

def powerCardTest(biasLevel):
    
    theDevice = LpdDevice()

    
    rc = theDevice.open('192.168.2.2', 6969)

    if rc != LpdDevice.ERROR_OK:
        print "Failed to open FEM device: %s" % (theDevice.errorStringGet())
        return
    
    print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
    
    # Update sensorBias if user provided new value via command line
    if biasLevel is not None:
        rc = theDevice.paramSet('sensorBias', biasLevel )
        if rc != LpdDevice.ERROR_OK:
            print "sensorBiasSet set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    
    print "Status:"
    print "    Low voltage  = ",
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
        print hvBias , "V"



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

    # Display temperature readings from PSU Card and Sensors
    print "Temperature readings:"

    (rc, theTemp) = theDevice.paramGet('powerCardTemp')
    if rc != LpdDevice.ERROR_OK:
        print "powerCardTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   PSU Card Temp: %.2f' % theTemp, '  C'

    (rc, theTemp) = theDevice.paramGet('sensorATemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorATemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor A Temp: %.2f' % theTemp, '  C'

    (rc, theTemp) = theDevice.paramGet('sensorBTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorBTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor B Temp: %.2f' % theTemp, '  C'
        
    (rc, theTemp) = theDevice.paramGet('sensorCTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorCTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor C Temp: %.2f' % theTemp, '  C'
        
    (rc, theTemp) = theDevice.paramGet('sensorDTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorDTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor D Temp: %.2f' % theTemp, '  C'
        
    (rc, theTemp) = theDevice.paramGet('sensorETemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorETemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor E Temp: %.2f' % theTemp, '  C'
        
    (rc, theTemp) = theDevice.paramGet('sensorFTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorFTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor F Temp: %.2f' % theTemp, '  C'
        
    (rc, theTemp) = theDevice.paramGet('sensorGTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorGTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor G Temp: %.2f' % theTemp, '  C'
        
    (rc, theTemp) = theDevice.paramGet('sensorHTemp')
    if rc != LpdDevice.ERROR_OK:
        print "sensorHTemp get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print '   Sensor H Temp: %.2f' % theTemp, '  C'

    # Display Fem, Digital, sensors voltages and current
    print "\nOutputs: "
    
    (rc, femVoltage) = theDevice.paramGet('femVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "femVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "   V FEM      : %.2f" % femVoltage, " V ",
    
    (rc, femCurrent) = theDevice.paramGet('femCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "femCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "%.2f" % femCurrent, " A"
     
        
    (rc, digitalVoltage) = theDevice.paramGet('digitalVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "digitalVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "   V Digital  : %.2f" % digitalVoltage, " V ",
    (rc, digitalCurrent) = theDevice.paramGet('digitalCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "digitalCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "%.2f" % digitalCurrent, " mA\n"
    

    
    (rc, sensorAVoltage) = theDevice.paramGet('sensorAVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "sensorAVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "   V Sensor A : %.2f" % sensorAVoltage, " V ",
    (rc, sensorACurrent) = theDevice.paramGet('sensorACurrent')
    if rc != LpdDevice.ERROR_OK:
        print "sensorACurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "%.2f" % sensorACurrent, " A"
    

    (rc, sensorBVoltage) = theDevice.paramGet('sensorBVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "sensorBVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "   V Sensor B : %.2f" % sensorBVoltage, " V ",
    (rc, sensorBCurrent) = theDevice.paramGet('sensorBCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "sensorBCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "%.2f" % sensorBCurrent, " A"

    
    (rc, sensorCVoltage) = theDevice.paramGet('sensorCVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "sensorCVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "   V Sensor C : %.2f" % sensorCVoltage, " V ",
    (rc, sensorCCurrent) = theDevice.paramGet('sensorCCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "sensorCCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "%.2f" % sensorCCurrent, " A"
    
    
    (rc, sensorDVoltage) = theDevice.paramGet('sensorDVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "sensorDVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "   V Sensor D : %.2f" % sensorDVoltage, " V ",
    (rc, sensorDCurrent) = theDevice.paramGet('sensorDCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "sensorDCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "%.2f" % sensorDCurrent, " A"

    
    
    (rc, sensorEVoltage) = theDevice.paramGet('sensorEVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "sensorEVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "   V Sensor E : %.2f" % sensorEVoltage, " V ",
    (rc, sensorECurrent) = theDevice.paramGet('sensorECurrent')
    if rc != LpdDevice.ERROR_OK:
        print "sensorECurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "%.2f" % sensorECurrent, " A"

    
    
    (rc, sensorFVoltage) = theDevice.paramGet('sensorFVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "sensorFVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "   V Sensor F : %.2f" % sensorFVoltage, " V ",
    (rc, sensorFCurrent) = theDevice.paramGet('sensorFCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "sensorFCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "%.2f" % sensorFCurrent, " A"

    
    
    (rc, sensorGVoltage) = theDevice.paramGet('sensorGVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "sensorGVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "   V Sensor G : %.2f" % sensorGVoltage, " V ",
    (rc, sensorGCurrent) = theDevice.paramGet('sensorGCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "sensorGCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "%.2f" % sensorGCurrent, " A"

    
    
    (rc, sensorHVoltage) = theDevice.paramGet('sensorHVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "sensorHVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "   V Sensor H : %.2f" % sensorHVoltage, " V ",
    (rc, sensorHCurrent) = theDevice.paramGet('sensorHCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "sensorHCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "%.2f" % sensorHCurrent, " A"

    print ""

    
    
    (rc, sensorBiasVoltage) = theDevice.paramGet('sensorBiasVoltage')
    if rc != LpdDevice.ERROR_OK:
        print "sensorBiasVoltage get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "   HV Bias    : %.2f" % sensorBiasVoltage, " V ",
    (rc, sensorBiasCurrent) = theDevice.paramGet('sensorBiasCurrent')
    if rc != LpdDevice.ERROR_OK:
        print "sensorBiasCurrent get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "%.2f" % sensorBiasCurrent, " uA"

    
    print "-- -- -- -- -- -- -- -- --"

    rc = theDevice.paramSet('tenGig0SourceMac', 3)
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0SourceMac Set failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    
    (rc, tenGig0SourceMac) = theDevice.paramGet('tenGig0SourceMac')
    if rc != LpdDevice.ERROR_OK:
        print "tenGig0SourceMac get failed rc=%d : %s" % (rc, theDevice.errorStringGet())
    else:
        print "tenGig0SourceMac : ", tenGig0SourceMac
        
    print "Closing Fem connection.. "        
    theDevice.close()

if __name__ == '__main__':

    if len(sys.argv) == 2:
        biasLevel = sys.argv[1]
    else:
        biasLevel = None
        
    powerCardTest(biasLevel)
    
