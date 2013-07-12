'''
uploadFirmware.py

Uploads a SystemACE image to a FEM along with a metadata
descriptor containing build / upload dates and a 32char
description string.

Created on June 24 - 2013

@author: mt47
'''
import sys, os.path, time, binascii, argparse

import ExcaliburFemTests.defaults as defaults
from FemClient.FemClient import *
from FemApi.FemSysaceConfig import FemSysaceConfig
import ExcaliburFemTests

def uploadFirmware(femHost, femPort, filename, desc, slot):

    crc = 0
    
    if (femHost == None):
        print "Error: No FEM address specified!"
        sys.exit(1)
    if (femPort == None):
        print "Error: No FEM port specified!"
        sys.exit(1)
    if (slot == None):
        print "Error: No FEM SystemACE slot specified!"
        sys.exit(1)
    
    # Configuration defaults
    chunkSize = 768432
    
    # TODO: MOVE THESE SOMEWHERE!
    CMD_WRITE_TO_CF = 2
    CMD_GET_FWADDR = 4
    CMD_VERIFY = 6
    
    FWIMAGE_OK = 0
    FWIMAGE_BUSY = 1
    FWIMAGE_BAD_MAGIC = 2
    FWIMAGE_BAD_SLOT = 3
    FWIMAGE_BAD_CRC = 4
    FWIMAGE_FS_OPEN_FAILED = 5
    FWIMAGE_FS_WRITE_FAILED = 6
    FWIMAGE_FS_READ_FAILED = 7
    FWIMAGE_FS_CLOSE_FAILED = 8
    
    # Get file size & last modified date
    size = os.path.getsize(filename)
    import struct
    
    fileTime = int(os.path.getmtime(filename))
    
    if (size == 0):
        print "Error: Can't open file or file empty!"
        sys.exit(1)
    
    # Connect to FEM
    try:
        theFem = FemClient((femHost, femPort), defaults.femTimeout)
    except FemClientError as errString:
        print "Error: FEM connection failed:", errString
        sys.exit(1)
    
    # Query FEM where to upload metadata / image bundle to
    response = theFem.commandSend(CMD_GET_FWADDR, 0);
    addr = response.payload[1]
    cfgAddr = addr
    print ""
    print "Upload address:      " + hex(addr)
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
    
    print "Uploading:          ",
    while True:
        print "#",
        sys.stdout.flush()
        
        chunk = f.read(chunkSize)
        if not chunk: break
    
        payload = [ord(val) for val in chunk]
        theFem.directWrite(theAddr=addr, thePayload=payload)
        addr += chunkSize
    
        crc = binascii.crc32(chunk, crc)    
    
    f.close()
    
    print ""
    
    crc = crc & 0xFFFFFFFF
    
    finishTime = time.time()
    duration = finishTime - uploadTime
    print "Upload time:         " + str(duration) + "s"
    print "Upload speed:        " + str((size / duration) / 1024) + "kb/s, " + str((size / duration) / 1024 / 1024) + "Mb/s"
    print "CRC32:               " + hex(crc)
    print ""
    print "Upload completed successfully."
    
    
    # Upload metadata with updated crc
    config = FemSysaceConfig(FemSysaceConfig.HEADER_MAGIC_WORD, size, slot, desc, fileTime, int(uploadTime), 0, crc, 0);
    configPayload = config.decodeAsInt()
    theFem.rawWrite(theAddr=cfgAddr, thePayload=configPayload)
    
    # Poll status for completion / error
    print "Writing image to CF...",
    sys.stdout.flush()
    theFem.commandSend(CMD_WRITE_TO_CF, 0)
    status = FWIMAGE_BUSY;
    while(status == FWIMAGE_BUSY):
        time.sleep(1)
        response = theFem.rawRead(cfgAddr + 0x3C, 1)
        status = response[0]
    
    if (status == FWIMAGE_OK):
        print "COMPLETED OK"
    else:
        print "ERROR CODE: ", status
    
    # Verify image on CF
    print "Verifying image on CF...",
    sys.stdout.flush()
    response = theFem.commandSend(CMD_VERIFY, 0)
    status = FWIMAGE_BUSY;
    while(status == FWIMAGE_BUSY):
        time.sleep(1)
        response = theFem.rawRead(cfgAddr + 0x3C, 1)
        status = response[0]
    
    if (status == FWIMAGE_OK):
        print "COMPLETED OK"
    else:
        print "ERROR CODE: ", status
    
    # Compare CRCs
    response = theFem.rawRead(cfgAddr + 0x38, 1)
    verifiedCrc = response[0]
    if (verifiedCrc == crc):
        print "CRC CHECK PASSED, UPLOAD SUCCESSFUL!"
    else:
        print "CRC CHECK FAILED!  UPLOAD CRC= " + hex(crc) + ", VERIFIED CRC= " + hex(verifiedCrc)
    
    return

# ----------------------


if __name__ == "__main__":

    # Create parser object and arguments, including defaults
    parser = argparse.ArgumentParser(description="uploadFirmware.py - Uploads SystemACE firmware image to remote FEM.", epilog="All parameters other than femhost / femport required.")
    parser.add_argument("--file", "-f", help="SystemACE firmware file", type=str, required=True, action='store')
    parser.add_argument("--slot", "-s", help="SystemACE slot number", type=int, choices=range(8), required=True, action='store')
    parser.add_argument("--desc", "-d", help="Description string for image", type=str, required=True, action='store')
    parser.add_argument("--address", "-a", help="[Optional] Set fem host IP (e.g. 10.0.0.1)", type=str, default=defaults.femHost, action='store')
    parser.add_argument("--port", "-p", help="[Optional] Set fem port (e.g. 6969)", type=int, default=defaults.femPort, action='store')
    args = parser.parse_args()

    uploadFirmware(args.address, args.port, args.file, args.desc, args.slot)