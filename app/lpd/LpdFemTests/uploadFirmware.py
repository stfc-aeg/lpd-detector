'''
uploadFirmware.py

Uploads a SystemACE image to a FEM along with a metadata
descriptor containing build / upload dates and a 32char
description string.

Created on June 24 - 2013

Adpated for LPD   August 2017  jac

@author: mt47
'''

######################################################
#
# 30/08/17  John Coughlan
#
# Upgraded from python 2 to 3 using tool "2to3"
#
# 25/08/17  John Coughlan
#
# Skipped checking of CRC as it is not actually verified with CF contents.
#
# 25/08/17  John Coughlan
#
# Using CMD_WRITE_TO_CF_MULTIPLE_SECTIONS for both FEM or TrainBuilder as this works with both.
#
# 24/08/17  John Coughlan
#
# Use buffer base address and size as provided by GbE server on board.
#
# Added board type argument
#
# Added nrSections field to FemSysaceConfig.py
#
# Added query_yes_no()
#
# 23/08/17  John Coughlan
#
# Added optional sectionNr field to FemSysaceConfig.py
# used if ace file is loaded in multiple sections due to limited on board memory
# needed for TrainBuilder where ace file is loaded in SRAM (as GbE server has no direct access to DDR2)
#
# 22/08/17  John Coughlan
#
# Pass socket timeout as argument.
# Increase socket timeout when loading larger ace files.
# Whilst ace is being transferred from ddr to cf card the gbe server socket does not respond.
# This means that although the ace update will still complete ok,  the script may crash with socket timeout error.
#
# 21/08/17  John Coughlan
#
# Tested upload working on LPD FEM.
#
######################################################

from __future__ import print_function, division

import sys, os.path, time, binascii, argparse

#import ExcaliburFemTests.defaults as defaults
#sys.path.append('defaults')
import defaults
#from . import defaults

from FemClient.FemClient import *
from FemApi.FemSysaceConfig import FemSysaceConfig
import ExcaliburFemTests


# TODO: MOVE THESE SOMEWHERE!
CMD_WRITE_TO_CF = 2
CMD_GET_FWADDR = 4
CMD_VERIFY = 6  
CMD_WRITE_TO_CF_MULTIPLE_SECTIONS = 7  
#CMD_GET_FWSIZE = 8
FWIMAGE_OK = 0
FWIMAGE_BUSY = 1
FWIMAGE_BAD_MAGIC = 2
FWIMAGE_BAD_SLOT = 3
FWIMAGE_BAD_CRC = 4
FWIMAGE_FS_OPEN_FAILED = 5
FWIMAGE_FS_WRITE_FAILED = 6
FWIMAGE_FS_READ_FAILED = 7
FWIMAGE_FS_CLOSE_FAILED = 8

# value will now be taken from board
BUFFER_SIZE_FEM = 0x40000000            # DDR2
BUFFER_SIZE_TRAINBUILDER = 0x400000     # half of SRAM
BUFFER_SIZE_TEST = 0x10000   
  
# special value used to indicate cf file can be closed
# artificially limits number file sections
LAST_SECTION_NUMBER = 0xFFFF

boardTypeStr = ["Undefined", "FEM", "TrainBuilder IO", "TrainBuilder Switch"]

def uploadFirmware(femHost, femPort, filename, desc, slot, timeout, board):

    crc = 0
    
    if (femHost == None):
        print("Error: No Board IP address specified!")
        sys.exit(1)
    if (slot == None):
        print("Error: No SystemACE slot specified!")
        sys.exit(1)
    if (filename == None):
        print("Error: No SystemACE File Name specified!")
        sys.exit(1)
    
    # Configuration defaults
    ##chunkSize = 768432
    #chunkSize = 10000    
    chunkSize = 0x4000  # 0x8000  # 0x4000  # chunk size must be even divisor of buffer size
    
    # Get file size & last modified date
    fileSize = os.path.getsize(filename)
    import struct
    
    fileTime = int(os.path.getmtime(filename))
    
    if (fileSize == 0):
        print("Error: Can't open file or file empty!")
        sys.exit(1)
    
    femTimeoutLong = timeout     # increase for larger ace file writing
    #print "Info: Fem socket Timeout = %d secs" %(femTimeoutLong)
    
    # Connect to FEM
    try:
        #theFem = FemClient((femHost, femPort), defaults.femTimeout)
        theBoard = FemClient((femHost, femPort), femTimeoutLong)
    except FemClientError as errString:
        print("Error: Board ethernet connection failed: %s" %(errString))
        sys.exit(1)
    
    # Verify board type
    getBoardType(theBoard)
    
    # Query FEM where to upload metadata / image bundle to
    
    #response = theBoard.commandSend(3, 0);
    response = theBoard.commandSend(CMD_GET_FWADDR, 0);
    bufferAddr = response.payload[1]
    bufferSize = response.payload[2]
    
    #print response
    
    print("CMD_GET_FWADDR: bufferAddr = $%08x ; buffersize = $%08x" %(bufferAddr, bufferSize))
    
    #print "CMD_GET_FWADDR reponse = %d" %(bufferAddr)
    
    #sys.exit(0)
    
    #response = theBoard.commandSend(CMD_GET_FWSIZE, 0);
    #bufferSize = response.payload
    #print "CMD_GET_FWSIZE reponse = %d" %(bufferSize)


    #addr = response.payload[1]
    #addr = response.payload[0]    
    #addr = value
    #addr = 0x40000000
    
    # buffer size of memory for uploading file
    #bufferSize = BUFFER_SIZE_FEM    
    #bufferSize = BUFFER_SIZE_TRAINBUILDER    
    #bufferSize = BUFFER_SIZE_TEST    
    
    cfgAddr = bufferAddr
    print("")
    print("Board type:  \t \t %s" %(boardTypeStr[board]))
    print("Board IP address: \t %s" %(femHost))
    print("Board UDP port:  \t %s" %(femPort))
    print("Socket Timeout (secs): \t %d" %femTimeoutLong)
    print("Upload buffer address: \t $%08x" %(bufferAddr))
    print("Upload buffer size:  \t $%08x" %(bufferSize))
    print("SystemACE slot: \t %d" %(slot))
    print("Ace File Name: \t \t %s" %(filename))
    print("File size (bytes): \t %d [$%08x]" %(fileSize,fileSize))
    
    #sys.exit(0)
    
    #uploadTime = time.time()
    #addr += FemSysaceConfig.configSize()
    
    # Chunk and upload image to addr + sizeof(metadata)
    f = open(filename, 'rb')
    if not f:
        print("Cannot open " + filename)
        sys.exit(1)
        
    nrChunksPerSection = bufferSize//chunkSize
    
    nrSections = fileSize//bufferSize + 1
        
    lastSectionSize = fileSize%bufferSize

    print("Chunk size (bytes): \t \t %d [$%08x] " %(chunkSize, chunkSize))
    print("Number of chunks per Section: \t %d \t \t" %(nrChunksPerSection))
    print("Number of file sections: \t %d" %(nrSections))
    print("Last Section size (bytes): \t %d [$%08x]" %(lastSectionSize, lastSectionSize))
    
    if (nrSections > 1):
        if (bufferSize%chunkSize) != 0:
            print("ERROR: Multiple file sections are required but Buffer size = $%08x is not evenly divisable by chunk size = $%08x" %(bufferSize, chunkSize))
            print("Quitting.")
            sys.exit(0)
             
    
    
    print("")
    print("################################################################################")
    print("You are about to replace the contents of Compact Flash card Firmware file slot #%d:"  %(slot))
    print("Please ensure all other Karabo ethernet access to this board is disabled during this process.")  
    print("")
    answer = query_yes_no("Do you wish to continue? (Y/N)")
    print("################################################################################")

    if answer:
        print("You have chosen to continue...")
    else:
        print("You have chosen NOT to continue. No action has been taken.")
        sys.exit(0)
        
    
    #sys.exit(0)

    #if (nrSections == 1):
        #femCmdWriteToCF = CMD_WRITE_TO_CF 
    #else:
        #femCmdWriteToCF = CMD_WRITE_TO_CF_MULTIPLE_SECTIONS
        
    # Multiple section loading works for either FEM or TrainBuilder
    femCmdWriteToCF = CMD_WRITE_TO_CF_MULTIPLE_SECTIONS

    for sectionNr in range(nrSections):
        
        
        # every section will have the metadata block before it
        addr = bufferAddr
        addr += FemSysaceConfig.configSize()
        
        if sectionNr == (nrSections-1):
            size = lastSectionSize
        else:            
            size = bufferSize
        i = 0
        countdown = (size//chunkSize) - i
        print("---------------------------------")
        print("Step 1: Uploading File to Memory buffer on board.")
        print("File Section %d out of %d" %(sectionNr+1, nrSections))
        print("Section Size = $%08x" %(size))
        print("Number of Chunks this section = %d" %(countdown))
        print("Uploading to onboard memory buffer: number of chunks counting down from %d to 0: " %(countdown))

        uploadTime = time.time()
        
        if 1:   # =0 for TESTING SCRIPT ONLY skipping upload step 
            #while True:
            while (i < nrChunksPerSection):
                #print "#",
                if (i%10) == 0:
                    #print(countdown, end=' ')  # python 2 only
                    print('%d ' %countdown, end='')    # python 3 (or2)
                    sys.stdout.flush()
                i = i+1
                countdown = (size//chunkSize) - i
                
                chunk = f.read(chunkSize)
                if sectionNr == (nrSections-1):
                    if not chunk: break
            
                payload = [ord(val) for val in chunk]
                theBoard.directWrite(theAddr=addr, thePayload=payload)
                ##theFem.rawWrite(theAddr=addr, thePayload=payload)
                addr += chunkSize
            
                crc = binascii.crc32(chunk, crc)    
        else:
            print("")
            print("WARNING: TEST ONLY Skipped the Upload step")
        
        if sectionNr == (nrSections-1): # actions for last section
            f.close()
            print("")
            print("Closing file.")
    
        print("")
        
        crc = crc & 0xFFFFFFFF
        
        finishTime = time.time()
        duration = finishTime - uploadTime
        print("Upload time:    %s  sec   " %(duration))
        print("Upload speed:   %s  kbytes/s  " %( (size / duration) / 1024))
        print("CRC32:          $%08x     " %(crc))
        print("")
        print("Upload to board memory buffer was completed successfully.")
    
           
        # special value used to indicate cf file can be closed
        #if sectionNr == (nrSections-1):
        #    sectionNr = LAST_SECTION_NUMBER
            
        # Upload metadata with updated crc
        config = FemSysaceConfig(FemSysaceConfig.HEADER_MAGIC_WORD, size, slot, sectionNr, nrSections, desc, fileTime, int(uploadTime), 0, crc, 0);
        configPayload = config.decodeAsInt()
        theBoard.rawWrite(theAddr=cfgAddr, thePayload=configPayload)
        
        downloadRate = 80.0    # kbytes/s as measured
        downloadEstimatedTime = (size/1024)/downloadRate
            
    
        if (sectionNr == 0):
            print("################################################################################")
            print("Step 2: Writing to CF card.")
            print("You are about to replace the contents of Compact Flash card Firmware file slot #%d:"  %(slot))
            print("Compact Flash Card will be overwritten.")  
            print("")
            answer = query_yes_no("Do you still wish to continue? (Y/N)")
            print("################################################################################")
            
            if answer:
                print("You have chosen to continue...")
                print("Writing ace image to Compact Flash card...")
                print("")
                print("Estimated time for loading section is %d secs" %(downloadEstimatedTime))
            else:
                print("You have chosen NOT to continue")
                print("The Compact Flash card contents have NOT been changed.")
                sys.exit(0)
        else:
            print("")
            print("Writing this section of ace image to Compact Flash card...")
            print("Estimated time for loading section is %d secs" %(downloadEstimatedTime))
            print("")
            
    
                    
        downloadTime = time.time()
        
        # Poll status for completion / error
        sys.stdout.flush()
        status = doFemCmdAndPollForCompletion(theBoard, femCmdWriteToCF, cfgAddr, 0x3C, 1)
    
        if sectionNr == (nrSections-1): # actions for last section
            if (status == FWIMAGE_OK):
                print("Done!")
            else:
                print("Error: $%08x" %(status))
        else:
            print("Number of bytes reported loaded to CF = $%08x" %(status))

        if 0:   # verify is not implement in gbe server yet.
            # Verify image on CF
            #print("Verifying image on CF...", end=' ')
            #sys.stdout.flush()
            status = doFemCmdAndPollForCompletion(theBoard, CMD_VERIFY, cfgAddr, 0x3C, 1)
    
    
        finishTime = time.time()
        duration = finishTime - downloadTime
        print("Compact Flash load time:    %s  sec   " %(duration))
        print("Load speed:   %s  kbytes/s  " %( (size / duration) / 1024))
        print("")

        if 0:   # verify is not implement in gbe server yet.
            # Compare CRCs
            response = theBoard.rawRead(cfgAddr + 0x38, 1)
            verifiedCrc = response[0]
            print("********************************************")
            if (verifiedCrc == crc):
                print("CRC CHECK OK, IMAGE UPLOAD SUCCESSFUL")
            else:
                print("CRC FAILED!  UPLOAD CRC= $%08x ; VERIFIED CRC= $%08x" %(crc, verifiedCrc))
            print("********************************************")
                
    print("********************************************")
    if (status == FWIMAGE_OK):                
        print("INFO: COMPACT FLASH MEMORY CARD FIRMWARE RELOAD SUCCESSFUL")
        if (boardTypeStr[board] == "FEM"):        
            print("To Reload the Board FPGA(s) with the new CF card image please use the python script: rebootFem.py")
        else:
            print("To Reload the Board FPGA(s) with the new CF card image please use the python script: TBReloadFromCF.py")
    else:
        print("*** ERROR: COMPACT FLASH MEMORY CARD RELOAD FAILED")
    print("********************************************")
    
    return

# ----------------------

# Sends a FEM command and then polls it at specified interval for completion
def doFemCmdAndPollForCompletion(fem, cmd, cfgAddr, offset, interval):
    
    response = fem.commandSend(cmd, 0)

    status = FWIMAGE_BUSY;
    while(status == FWIMAGE_BUSY):
        time.sleep(interval)
        response = fem.rawRead(cfgAddr + offset, 1)
        status = response[0]
        #print "doFemCmdAndPollForCompletion ; status = %d"  %(status)      

    #if (status == FWIMAGE_OK):
        #print "Done!"
    #else:
        #print "Error: $%08x" %(status)
        
    return status

# Get Board Type
# Use Readonly registers to get board type
def getBoardType(theBoard):

    board_type = 0
    
    return board_type

def query_yes_no(question, default=None):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        
        if sys.version_info[0] < 3:
            choice = raw_input().lower()
        else:
            choice = input().lower()
        
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
# ----------------------    

if __name__ == "__main__":

    # Create parser object and arguments, including defaults
    parser = argparse.ArgumentParser(description="uploadFirmware.py - Uploads SystemACE firmware image to Compact Flash memory card on board via Ethernet.", epilog="All parameters other than udp_port, socket_timeout and desc are required.")
    parser.add_argument("--board_type", "-b", help="Board Type (1=FEM; 2=TB_IO; 3=TB_Switch)", type=int, choices=list(range(1,4)), required=True, action='store')
    parser.add_argument("--ace_file", "-f", help="SystemACE firmware file", type=str, required=True, action='store')
    parser.add_argument("--ace_slot", "-s", help="SystemACE slot number", type=int, choices=list(range(1,8)), required=True, action='store')
    parser.add_argument("--desc", "-d", help="Description string for image", type=str, default="lpdfem", action='store')
    parser.add_argument("--ip_addr", "-a", help="Set fem host IP (e.g. 192.168.2.2)", type=str, required=True, action='store')
    parser.add_argument("--udp_port", "-p", help="[Optional] Set fem port (e.g. 6969)", type=int, default=defaults.femPort, action='store')
    parser.add_argument("--socket_timeout", "-t", help="[Optional] Set IP socket timeout (secs) ", type=int, default=600, action='store')
    args = parser.parse_args()

    uploadFirmware(args.ip_addr, args.udp_port, args.ace_file, args.desc, args.ace_slot, args.socket_timeout, args.board_type)