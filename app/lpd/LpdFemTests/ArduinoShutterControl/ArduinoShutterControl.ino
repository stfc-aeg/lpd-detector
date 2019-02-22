/*
 * ------------------------------
 *      ArduinoShutterControl
 * ------------------------------
 *
 * This is the Arduino code written to control the shutter 
 * for the Diamond 2014 Beam tests (October 8-October 10).
 * It was based upon the following example:
 *    (MultipleSerialServoControl)
 * Dependencies:
 *   Arduino 0017 or higher
 *     (http://www.arduino.cc/en/Main/Software)
 *   Python servo.py module
 *     (http://principialabs.com/arduino-python-4-axis-servo-control/)
 *
 * Created:  23 December 2009
 * Author:   Brian D. Wendt
 *   (http://principialabs.com/)
 * Version:  1.1
 * License:  GPLv3
 *   (http://www.fsf.org/licensing/)
 */

// Import the Arduino Servo library
#include <Servo.h> 

Servo servo1;

int angle = 180;

void setup() 
{ 
  // Attach each Servo object to a digital pin
  servo1.attach(9);
  pinMode(2, INPUT);
  
  // Open the serial connection, 9600 baud
  Serial.begin(9600);

  servo1.write(angle);  // Open
} 

void loop()
{
  // Wait for serial input
  if (Serial.available() > 0) {

    // Read the byte
    int choice = Serial.read();
    if ((choice == 0) || (choice == 1))
    {
      if (choice == 0)
        angle = 180;    // Shut
      else
        angle = 70;     // Open

      servo1.write(angle);
    }

  }
}
