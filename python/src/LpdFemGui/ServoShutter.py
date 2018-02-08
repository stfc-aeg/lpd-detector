import sys, serial

class ServoShutter():
    ''' Class to control Arduino shutter for Diamond beam time '''
    
    def __init__(self, usbport):
        # Set up serial baud rate
        try:
            self.ser = serial.Serial(usbport, 9600, timeout=1)
            #print >> sys.stderr, "Connected to Arduino shutter"
        except Exception as e:
            raise Exception("Serial Connection Error: %s" % e)

    def __del__(self):
        # Close serial connection, if open
        try:
            if self.ser.isOpen():
                self.ser.close()
        except Exception:
            # Suppress any error upon exit
            pass
        
    def move(self, position):
        ''' Moves the shutter to the supplied position
            0=shut, 1=open '''

        if (position == b'\0' or position == b'\1'):
            try:
                self.ser.write(position)
            except Exception as e:
                raise Exception("Error %s shutter: %s" % (("closing" if position is 0 else "opening"), e))
            #print >> sys.stderr, "Exercising the shutter by %s it.." % (("closing" if position is 0 else "opening"))
        else:
            raise Exception("Shutter position must be an integer, either 0 (shut) or 1 (open)")

