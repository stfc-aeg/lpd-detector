'''
uploadFirmware.py

Uploads a SystemACE image to a FEM along with a metadata
descriptor containing build / upload dates and a 32char
description string.

Created on June 24 - 2013

@author: mt47
'''
import sys, os.path, time, binascii

import ExcaliburFemTests.defaults as defaults
from FemClient.FemClient import *
from FemApi.FemSysaceConfig import FemSysaceConfig

defaults.parseArgs()
crc = 0

# Configuration defaults
chunkSize = 768432

# Put these somewhere better
CMD_WRITE_TO_CF = 2
CMD_GET_FWADDR = 4

# TODO: Accept these as parameters!
# ----------------------------------
# 'Firmware' file to upload
filename = "../../rev0.ace"

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
cfgAddr = addr
print ""
print "Upload address:      "+ hex(addr)
print "SystemACE slot:     ", slot
print "Image size (bytes): ", size

uploadTime = time.time()
addr += FemSysaceConfig.configSize()

# Chunk and upload image to addr + sizeof(metadata)
f = open(filename, 'rb')
if not f:
    print "Cannot open " + filename
    sys.exit(1)
    
print "Chunk size (bytes): ", chunkSize

print "UPLOADING..."
while True:
    chunk = f.read(chunkSize)
    if not chunk: break

    payload = [ord(val) for val in chunk]
#    theFem.directWrite(theAddr=addr, thePayload=payload)
    addr += chunkSize

    crc = binascii.crc32(chunk, crc)    

f.close()

crc = crc &0xFFFFFFFF

finishTime = time.time()
duration = finishTime - uploadTime
print "Upload time:         " + str(duration) + "s"
print "Upload speed:        " + str((size/duration)/1024) + "kb/s, " + str((size/duration)/1024/1024) + "Mb/s"
print "CRC32:               " + hex(crc)

# Upload metadata with updated crc
config = FemSysaceConfig(FemSysaceConfig.HEADER_MAGIC_WORD, size, slot, desc, fileTime, int(uploadTime), 0, crc, 0);
configPayload = config.decodeAsInt()
theFem.rawWrite(theAddr=cfgAddr, thePayload=configPayload)

# Issue firmware upload command
#theFem.commandSend(CMD_WRITE_TO_CF, 0)
