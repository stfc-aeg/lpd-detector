import sys
import os
import time
import optparse

from femClient.FemClient import  FemClient
from femApi.femTransaction import FemTransaction

# Parse command line arguments
parser = optparse.OptionParser()
parser.add_option("-n", "--numloops", dest="numLoops", type="int", default=1000)
(options, args) = parser.parse_args()

# Make stdout unbuffered
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

# Transaction parameters
#addr = 0x81440000  # LEDs
addr = 0x8b900000  # SRAM
lengthArr = [1, 4, 8, 16, 32, 64, 128, 256]
numLoops = options.numLoops
bus = FemTransaction.BUS_RAW_REG
width = FemTransaction.WIDTH_LONG


# Lists for results
writeDeltaT = []
writeBytes  = []
readDeltaT = []
readBytes  = []


# Open FEM connection

host = '192.168.1.10'
port = 6969

theFem = FemClient((host, port))

if theFem != None:
    print "Connected OK..."
else:
    print "ERROR: connection failed"    
    sys.exit(1)
    
# Write transaction test
print "Running write transaction tests",
for length in lengthArr:

    (payloadByteLen,payloadFormat) = FemTransaction.widthEncoding[width]
    totalBytes = payloadByteLen * length * numLoops
    start = time.time()
    for i in range(0, numLoops):
        values = tuple(range(0, length))
        ack = theFem.write(bus, width, addr, values)
    end = time.time()
    deltaT = end - start
    writeDeltaT.append(deltaT)
    writeBytes.append(totalBytes)
    print ".",

print " done."    
    
# Read transaction test
print "Running read transaction tests ",
for length in lengthArr:

    (payloadByteLen,payloadFormat) = FemTransaction.widthEncoding[width]
    totalBytes = payloadByteLen * length * numLoops
    start = time.time()
    for i in range(0, numLoops):
        values = theFem.read(bus, width, addr, length)
    end = time.time()
    deltaT = end - start
    readDeltaT.append(deltaT)
    readBytes.append(totalBytes)
    print ".",
    
print " done."

# Print results
print ""
print "                 Write                          Read"
print "Length   Time     Rate       Thru      Time     Rate       Thru"
print "----------------------------------------------------------------"

for i in range(0, len(lengthArr)): 
    print "%5d  %6.3f  %7.1f  %10.1f   %6.3f  %7.1f  %10.1f" % \
        (lengthArr[i], writeDeltaT[i], numLoops / writeDeltaT[i], writeBytes[i] / writeDeltaT[i],
         readDeltaT[i], numLoops / readDeltaT[i], readBytes[i] / readDeltaT[i]) 

# Close the connection
theFem.close()


