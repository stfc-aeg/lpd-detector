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
import struct

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
print ""
print ""
print "Upload address:      "+ hex(addr)
print "SystemACE slot:     ", slot
print "Image size (bytes): ", size

# Build metadata
uploadTime = time.time()
config = FemSysaceConfig(FemSysaceConfig.HEADER_MAGIC_WORD, size, slot, desc, fileTime, int(uploadTime), 0, 0, 0);

# Upload metadata to addr
configPayload = config.decodeAsInt()
theFem.rawWrite(theAddr=addr, thePayload=configPayload)
addr += config.getSize()

# Chunk and upload image to addr + sizeof(metadata)
f = open(filename, 'rb')
if not f:
    print "Cannot open " + filename
    sys.exit(1)
    
thisChunk = 1
print "Chunk size:         ", chunkSize
print "Uploading:          ",
while True:
    chunk = f.read(chunkSize)
    if not chunk: break
    
    # mangle (bad because it will only work with exact sizes of chunk :(
    #format = '!%dI' % (chunkSize / 4)
    #payload = struct.unpack(format, chunk)
    #print type(payload), len(payload), type(payload[0])
    #theFem.rawWrite(theAddr=addr, thePayload=payload)
    
    # Better
    payload = [ord(val) for val in chunk]
    theFem.directWrite(theAddr=addr, thePayload=payload)
    addr += chunkSize
    
    thisChunk += 1
    print ".",
    
f.close()
print ""

finishTime = time.time()
print "Upload time:         " + str(finishTime - uploadTime) + "s"

# Issue firmware upload command
#theFem.commandSend(CMD_WRITE_TO_CF, 0)
