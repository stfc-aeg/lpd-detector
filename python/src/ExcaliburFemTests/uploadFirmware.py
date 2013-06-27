'''
uploadFirmware.py

Uploads a SystemACE image to a FEM along with a metadata
descriptor containing build / upload dates and a 32char
description string.

Created on June 24 - 2013

@author: mt47
'''
import sys, os.path, time

import ExcaliburFemTests.defaults as defaults
from FemClient.FemClient import *
from FemApi.FemSysaceConfig import FemSysaceConfig

defaults.parseArgs()

# Configuration defaults
chunkSize = 512

# Put these somewhere better
CMD_WRITE_TO_CF = 2
CMD_GET_FWADDR = 4

# TODO: Accept these as parameters!
# ----------------------------------
# 'Firmware' file to upload
filename = "test.txt"

# Description
desc = "TEST_UPLOAD"

# SystemACE slot
slot = 1
# ----------------------------------

# Get file size & last modified date
size = os.path.getsize(filename)
fileTime = int(os.path.getmtime(filename))

if (size==0):
    print "FILE EMPTY, ABORTING"
    sys.exit(1)

# Connect to FEM
try:
    theFem = FemClient((defaults.femHost, defaults.femPort), defaults.femTimeout)
except FemClientError as errString:
    print "Error: FEM connection failed:", errString
    sys.exit(1)

# Query FEM where to upload metadata / image bundle to
response = theFem.commandSend(CMD_GET_FWADDR, 0);
addr = response.payload[1]
print "Uploading firmware metadata to "+ hex(addr)
print "SystemACE slot: ", slot
print "Image size (bytes): ", size

# Build metadata
uploadTime = int(time.time())
#config = FemSysaceConfig(FemSysaceConfig.HEADER_MAGIC_WORD, size, slot, desc, fileTime, uploadTime, 0, 0, 0);
config = FemSysaceConfig(FemSysaceConfig.HEADER_MAGIC_WORD, size, slot, 0, 0, 0, 0, fileTime, uploadTime, 0, 0, 0);

# Upload metadata to addr
configPayload = config.decode()
theFem.rawWrite(theAddr=addr, thePayload=configPayload)

# Chunk and upload image to addr + sizeof(metadata)
f = open(filename, 'rb')
if not f:
    print "Cannot open " + filename
    sys.exit(1)
    
thisChunk = 1
while True:
    chunk = f.read(chunkSize)
    if not chunk: break
    theFem.rawWrite(theAddr=addr, thePayload=chunk)
    addr += chunkSize
    thisChunk += 1
    print "Wrote chunk ", thisChunk
    
f.close()

# Issue firmware upload command
#theFem.commandSend(CMD_WRITE_TO_CF, 0)
