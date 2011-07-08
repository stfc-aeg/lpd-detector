import time

from femClient.FemClient import  FemClient
from femApi.femTransaction import FemTransaction

# Open FEM connection

host = '192.168.1.10'
port = 6969

theFem = FemClient((host, port))

if theFem != None:
    print "Connected OK..."
    
    
# Setup parameters for write transaction test
bus = FemTransaction.BUS_RAW_REG
width = FemTransaction.WIDTH_LONG
state = FemTransaction.STATE_WRITE
addr = 0x81440000
numLoops = 1000

print "Starting write transaction test, num loops =", numLoops
start = time.time()
for i in range(0, numLoops):
    values = i%256,
    ack = theFem.write(bus, width, addr, values)
end = time.time()
deltaT = end - start
print "Done: %d writes took %.3f secs, rate = %.1f per sec " % (numLoops, deltaT, numLoops / deltaT)
    
# Setup parameters for read transaction test
bus = FemTransaction.BUS_RAW_REG
width = FemTransaction.WIDTH_LONG
state = FemTransaction.STATE_WRITE
addr = 0x81440000
length = 1
numLoops = 1000

print "Starting read transaction test, num loops =", numLoops
start = time.time()
for i in range(0, numLoops):
    values = theFem.read(bus, width, addr, length)
end = time.time()
deltaT = end - start
print "Done: %d read took %.3f secs, rate = %.1f per sec " % (numLoops, deltaT, numLoops / deltaT)
    
# Close the connection

theFem.close()

