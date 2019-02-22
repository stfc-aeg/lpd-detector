import sys
import os
import time
import optparse
import random

from FemClient.FemClient import  *
from FemApi.FemTransaction import FemTransaction

# Parse command line arguments
parser = optparse.OptionParser()
parser.add_option("-n", "--numloops", dest="numLoops", type="int", default=1000,
                  help="set number of transaction test loops to execute", metavar="LOOPS")
parser.add_option('-b', "--bus", dest="bus", type="string", default="raw",
                  help="specify which FEM bus to access")
parser.add_option('-a', "--address", dest="address", type="int", default=None,
                  help="set address to access")
(options, args) = parser.parse_args()

# Make stdout unbuffered
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

# Setup transaction parameters, depending on chosen bus

if options.bus == 'raw':

    if options.address == None:
        #addr = 0x81440000  # LEDs
        addr = 0x8b900000  # SRAM
    else:
        addr = options.address
        
    lengthArr = [1, 4, 8, 16, 32, 64, 128, 256]
    bus = FemTransaction.BUS_RAW_REG

elif options.bus == 'rdma':
    
    if options.address == None:
        addr = 0
    else:
        addr = options.address
        
    lengthArr = [1, 4]
    bus = FemTransaction.BUS_RDMA
    
else:
    
    print "Unrecognised bus sepcified:", options.bus
    sys.exit(1)
    
numLoops = options.numLoops
width = FemTransaction.WIDTH_LONG


# Lists for results
writeDeltaT = []
writeBytes  = []
readDeltaT = []
readBytes  = []


# Open FEM connection

host = '127.0.0.1'
port = 6996
timeout = 1.0

try:
    theFem = FemClient((host, port), timeout)
except FemClientError as errString:
    print "Error: connection failed:", errString
    sys.exit(1)
    
    
# Write transaction test
print "Running write transaction tests",
for length in lengthArr:

    (payloadByteLen,payloadFormat) = FemTransaction.widthEncoding[width]
    totalBytes = payloadByteLen * length * numLoops
    start = time.time()
    for i in range(0, numLoops):
        values = tuple(range(0, length))
#        values = tuple([ int(random.uniform(0,4096)) for i in range(0, length)])
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


