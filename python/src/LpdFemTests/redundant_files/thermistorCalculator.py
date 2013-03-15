'''
    Author: ckd27546
    
    Created on 29 November 2012
    
    thermistorCalculator.py: Supports the calculation of the variables required for converting a given voltage read 
                                from the thermistor resistance into its equivalent temperature value. 
'''

from math import log

class thermistorCalculator():
    
    def calculateResistance(self, aVoltage):
        '''
            Calculates the resistance for a given voltage (Utilised by the temperature sensors, on board as well as each ASIC module)
        '''
        # Define the supply voltage and the size of resistor inside potential divider
        vCC = 5
        resistance = 15000
        # Calculate resistance of the thermistor
        resistanceTherm = ((resistance * aVoltage) / (vCC-aVoltage))
        return resistanceTherm
    
    def calculateBeta(self, tempOne, tempTwo, resistanceOne, resistanceTwo):
        ''' Calculate the Beta value for the known resistance at two different temperatures.
            Where:
                resistanceOne is the resistance at tempOne's temperature
                resistanceTwo is the resistance at tempTwo's temperature
            e.g:
                calculateBeta(0, 25, 2.905, 1) => T0, 0C, 2.905 - T1, 25C, 1
            Note:
                2.905 and 1 are resistances relative to each other (abs values: 29050 vs 10000 Ohms) 
        '''
        # Calculate the two denominator parts
        denominatorOne = (1 / (273.15 + tempOne))
        denominatorTwo = (1 / (273.15 + tempTwo))
#        print denominatorOne, denominatorTwo
        # Calculate the natural logarithm part
        naturalLog = log(resistanceOne / resistanceTwo)
#        print naturalLog
        # Calculate Beta
        Beta = (1 / (denominatorOne - denominatorTwo) ) * naturalLog
        return Beta

    def calculateTemperature(self, Beta, resistanceOne):
        ''' e.g. calculateTemperature(3630, 26000) = 3.304 degrees Celsius '''
        # Define constants since resistance and temperature is already known for one point
        resistanceZero = 10000
        tempZero = 25.0

        invertedTemperature = (1.0 / (273.1500 + tempZero)) + ( (1.0 / Beta) * log(float(resistanceOne) / float(resistanceZero)) )

        # Invert the value to obtain temperature (in Kelvin) and subtract 273.15 to obtain Celsius
        return (1 / invertedTemperature) - 273.15

if __name__ == "__main__":
    
    myObject = thermistorCalculator()
#    # Define a voltage and calculate its equivalent resistance
#    aVoltage = 2
#    resistanceOne = myObject.calculateResistance(aVoltage)
    
    # Calculator template based upon    
    Beta = 3474
    resistanceZero = 10000
    resistanceOne = 26000
    
    # Calculate a temperature
    theTemperature = myObject.calculateTemperature(Beta, resistanceOne)
    
    print "The calculated temperature is:", theTemperature
    
    # Calculate Beta example
#    tempOne = 0
#    tempZero = 25
#    tempTwo = 25
#    resistanceOne = 2.905
#    resistanceTwo = 1
#    Beta = myObject.calculateBeta(tempOne, tempTwo, resistanceOne, resistanceTwo)
#    print "Beta = ", Beta
    