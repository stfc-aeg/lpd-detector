'''
Created on Sep 23, 2011

@author: tcn45
'''
from FemApi.FemTransaction import FemTransaction
from FemTests.FemBrokenClient import FemBrokenClient

host = '127.0.0.1'
port = 5000
wait = False

theFem = FemBrokenClient((host, port))

values = 1, 2, 3, 4
theTransaction = FemTransaction(cmd = FemTransaction.CMD_ACCESS,  bus=FemTransaction.BUS_RDMA, 
                                state=FemTransaction.STATE_WRITE, width=FemTransaction.WIDTH_LONG,
                                addr = 0x1234, payload=values)

## Send transaction without payload
print "Sending transaction without payload ..."
theFem.sendWithoutPayload(theTransaction)
if wait: raw_input("Hit return to continue ...")

## Send transaction with incomplete payload
print "Sending transaction with incomplete payload ..."
partialLen = len(values) - 2
theFem.sendPartialPayload(theTransaction, partialLen)
if wait: raw_input("Hit return to continue ...")

# Send transaction with excess payload 
print "Sending transaction with excessive payload ..."
excessLen = 4
theFem.sendExcessPayload(theTransaction, excessLen)
if wait: raw_input("Hit return to continue ...")

# Send a well-formed transaction
print "Sending well-formed transaction"
theFem.send(theTransaction=theTransaction)

if wait: raw_input("Hit return to finish ... ")

theFem.close()
