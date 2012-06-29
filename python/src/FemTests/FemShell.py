'''
Created on 22 Mar 2011

@author: tcn
'''

import cmd
import os
import readline
import string
import time
import code

from FemClient.FemClient import FemClient, FemClientError
from FemApi.FemTransaction import FemTransaction
from FemApi.FemConfig import FemConfig

class FemShell(cmd.Cmd,object):
    
    connectedFem = None;
    timerEnabled = False;
    
    busEncoding = { 'EEPROM' : FemTransaction.BUS_EEPROM ,
                    'I2C'    : FemTransaction.BUS_I2C  ,
                    'RAW'    : FemTransaction.BUS_RAW_REG ,
                    'REG'    : FemTransaction.BUS_RAW_REG,
                    'RDMA'   : FemTransaction.BUS_RDMA,
                    'DIRECT' : FemTransaction.BUS_DIRECT
                  } 
    
    widthEncoding = { 'BYTE' : FemTransaction.WIDTH_BYTE, 
                      'WORD' : FemTransaction.WIDTH_WORD, 
                      'LONG' : FemTransaction.WIDTH_LONG
                    }
    
    acqModeEncoding = { 'NORMAL' : FemTransaction.ACQ_MODE_NORMAL,
                        'BURST'  : FemTransaction.ACQ_MODE_BURST,
                        'RX'     : FemTransaction.ACQ_MODE_RX_ONLY,
                        'TX'     : FemTransaction.ACQ_MODE_TX_ONLY,
                        'UPLOAD' : FemTransaction.ACQ_MODE_UPLOAD                           
                      }
    
    acqStatusEncoding = { 0 : 'IDLE',
                          1 : 'CONFIG BUSY',
                          2 : 'NORMAL ACQ',
                          3 : 'UPLOAD ACQ',
                          4 : 'STOPPING ACQ'
                        }
    
    def __init__(self, completekey='tab', stdin=None, stdout=None, cmdqueue=None):
      
        cmd.Cmd.__init__(self, completekey, stdin, stdout)
        
        self.pystate = {}
        
        self.loopRecurseDepth = 0

        if stdin or cmdqueue:
            self.use_rawinput = 0
            self.prompt = ''
            self.preLoopMsg = None
            self.postLoopMsg = None
        else:
            self.prompt = "[FemShell] $ "
            self.preLoopMsg = "\nWelcome to the FEM Interactive Shell\n"
            self.postLoopMsg = "\nFemShell exiting"
         
        if cmdqueue:
            self.cmdqueue = cmdqueue   
               
    def preloop(self):
        if self.preLoopMsg:
            print self.preLoopMsg
        super(FemShell, self).preloop()
        
    def postloop(self):
        if self.postLoopMsg:
            print self.postLoopMsg
        super(FemShell, self).postloop()
 
    def emptyline(self):
        pass
    
    def do_exit(self, s):
        '''
        Exits the shell (Ctrl-D can also be used)
        '''
        return True;
    
    def help_exit(self):
        print self.do_exit.__doc__
        
    do_EOF = do_exit
    help_EOF = help_exit
    do_quit = do_exit
    help_quit = help_exit
    do_end = do_exit
           
    def help_help(self):
        print "Provides help for all commands, or type help <topic> for a specific command"
        
    def do_shell(self, s):
        '''
        Executes a system shell command
        Syntax: shell <cmd>
        '''
        os.system(s)
        
    def help_shell(self):
        print self.do_shell.__doc__
    
    def do_wait(self, s):
        '''
        wait <time>: Waits for the specified time in seconds
        time can be non-integer value in secs, e.g. 0.1 
        '''
        waitParams = s.split()
        if len(waitParams) != 1:
            print "*** error: invalid wait syntax (wait <secs>)"
            return
        try:
            waitTime = float(waitParams[0])
        except:
            print "*** error: invalid wait syntax (wait <secs>)"
            return
        time.sleep(waitTime)
        
    def help_wait(self):
        print self.do_wait.__doc__

    def do_py(self, s):
        '''
        Launches an embedded python shell
        '''
        self.pystate['self'] = self
        console = code.InteractiveConsole(locals=self.pystate)
        try:
            cprt = 'Type "help", "copyright", "credits" or "license" for more information.'
            console.interact(banner = "Python %s on %s\n%s\n(%s)" % 
                             (sys.version, sys.platform, cprt, self.__class__.__name__))
        except:
            print "Embedded console terminated"
            pass
        
    def help_py(self):
        print self.do_py.__doc__
                            
    def do_for(self, s):
        '''
Creates for-loop style iteration over a set of commands.

Syntax  : for <var> in <list_expr>
Where   :     <var>      = variable name to be substituted in iteration
             <list_expr> = python expression that evaluates to a list, e.g. range(1,10,1) or [1,2,3]
             
The loop is closed with the \'end\' command. Nested loops are permitted provided variable
names are lexicographically unique. Substitution is performed within the block where the 
expression $<var> is found. Indentation of loops is optional.

Example:
    for i in range(0,10,1)
       echo $i
       for j in range(0,5,1)
          echo $i $j
       end
    end
        '''

        forParams = s.split()
        if len(forParams) < 3 or forParams[1] != 'in':
            print "***: invalid for syntax (for <var> in <list expression>)"
            return
        try:
            iterList = eval(' '.join(forParams[2:]))
        except:
            print "***: invalid for syntax (for <var> in <list expression>)"
            return

        if not isinstance(iterList, list):
            print "***: invalid for syntax (for <var> in <list expression>)"
            return
        
        iterVarSubsPat = '$' + forParams[0]
        
        inLoop = True
        cmdQueue = []
        while inLoop:

            if self.cmdqueue:
                line = self.cmdqueue.pop(0)
            else:
                if self.use_rawinput == 1:
                    loopPrefix = ('    ' * (self.loopRecurseDepth + 1)) + '+> '
                    line = raw_input(loopPrefix)
                else:
                    line = self.stdin.readline()
                    line = line[:-1] # chop \n

            line = line.strip()
            cmd = line.split()[0]
            
            if cmd == 'for':
                self.loopRecurseDepth += 1
 
            if cmd == 'end':
                    if self.loopRecurseDepth > 0:
                        self.loopRecurseDepth -= 1
                    else:
                        inLoop = False
            cmdQueue.append(line)
        
        for iterVarVal in iterList:
            subsQueue = [cmd.replace(iterVarSubsPat, str(iterVarVal)) for cmd in cmdQueue]
            subShell = FemShell(stdin=self.stdin, cmdqueue=subsQueue)
            subShell.cmdloop()
  
    def help_for(self):
        print self.do_for.__doc__
        
    def help_end(self):
        print "Terminates a for loop"
         
    def do_echo(self, s):
        '''
        Echoes any output back to user
        '''
        print s
               
    def help_echo(self):
        print self.do_echo.__doc__
           
    def do_open(self, s):
        '''
        Opens a new connection to a FEM.
        Syntax: open <addr> <port>
        '''
         
        params = s.split()
        if len(params) != 2:
            print "*** Invalid number of arguments"
            return
        host = params[0] # '127.0.0.1'
        try:
            port = int(params[1])
        except ValueError:
            print "***: parameter 2 (port) must be a number"
            return
        
        try:
            self.__class__.connectedFem = FemClient((host, port))
        except FemClientError as (strerror):
            print "FEM connection error:", strerror
            self.__class__.connectedFem = None
             
    def help_open(self):
        print self.do_open.__doc__
    
    def do_write(self, s):
        '''
        Writes data to a FEM using the command protocol.
        Syntax: write <bus> <width> <addr> <values...> 
        where bus = GPIO, I2C, RAW, REG, RDMA, EEPROM, DIRECT
              width = BYTE, WORD, LONG
        '''
        
        params = s.split()
        if len(params) < 4:
            print "*** Invalid number of arguments"
            return
        
        #  Decode bus parameter string to bus ID
        busStr = string.upper(params[0])
        if FemShell.busEncoding.has_key(busStr):
            bus = FemShell.busEncoding[busStr]
        else:
            print "*** bus parameter not recognized"
            return

        # Decode width parameter string to width ID
        widthStr = string.upper(params[1])
        if FemShell.widthEncoding.has_key(widthStr):
            width = FemShell.widthEncoding[widthStr]
        else:
            print "*** width parameter not recognized"
            return
        
        # Get address and values from remaining parameters, allowing hex conversion to int
        try:
            addr = int(params[2], 0)
            values = tuple([int(param, 0) for param in params[3:]])
        except ValueError:
            print "*** address and value parameters must be integer"
            return
            
        # Issue the write command to the FEM
        if self.__class__.connectedFem == None:
            print "*** Not connected to a FEM"
            return

        try:
            if self.timerEnabled: t0 = time.time()        
            ack = self.__class__.connectedFem.write(bus, width, addr, values)
            if self.timerEnabled: deltaT = time.time() - t0
            print "Got ack: ", ['0x{:X}'.format(result) for result in ack]
            if self.timerEnabled: print "Transaction took %.3f secs" % deltaT 

        except FemClientError as e:
            if e.errno == FemClientError.ERRNO_SOCK_CLOSED:
                print "*** Error, FEM has closed the client connection"
                self.do_close(None)
            elif e.errno == FemClientError.ERRNO_SOCK_ERROR:
                print "*** Socket error on FEM connection:", e.msg
                self.do_close(None)
            else:
                print "*** FEM Exception:", e, 'errno=', e.errno

            
    def help_write(self):
        print self.do_write.__doc__

    def do_read(self, s):
        '''
        Reads data from a FEM using the command protocol.
        Syntax: read <bus> <width> <addr> <numReads> 
        where bus = GPIO, I2C, RAW, REG, RDMA
              width = BYTE, WORD, LONG
        '''        
        params = s.split()
        if len(params) < 4:
            print "*** Invalid number of arguments"
            return
        
        #  Decode bus parameter string to bus ID
        busStr = string.upper(params[0])
        if FemShell.busEncoding.has_key(busStr):
            bus = FemShell.busEncoding[busStr]
        else:
            print "*** bus parameter not recognized"
            return

        # Decode width parameter string to width ID
        widthStr = string.upper(params[1])
        if FemShell.widthEncoding.has_key(widthStr):
            width = FemShell.widthEncoding[widthStr]
        else:
            print "*** width parameter not recognized"
            return

        # Get address and read length from remaining params, allowing for hex conversion
        try:
            addr   = int(params[2], 0)
            length = int(params[3], 0)
        except ValueError:
            print "*** parameters must be integer"
            return
        
        # Issue read command to FEM  
        if self.__class__.connectedFem == None:
            print "*** Not connected to a FEM"
            return  

        try:
            if self.timerEnabled: t0 = time.time()
            values = self.__class__.connectedFem.read(bus, width, addr, length)
            if self.timerEnabled: deltaT = time.time() - t0
           
            try: 
                print "Got results:", ['0x{:X}'.format(result) for result in values]
            except TypeError:
                print "Can't decode results", values
                
            if self.timerEnabled: print "Transaction took %.3f secs" % deltaT
            
        except FemClientError as e:
            if e.errno == FemClientError.ERRNO_SOCK_CLOSED:
                print "*** Error, FEM has closed the client connection"
                self.do_close(None)
            elif e.errno == FemClientError.ERRNO_SOCK_ERROR:
                print "*** Socket error on FEM connection:", e.msg
                self.do_close(None)
            else:
                print "*** FEM Exception:", e, 'errno=', e.errno
      
        
    def help_read(self):
        print self.do_read.__doc__
        
    def do_close(self, s):
        '''
        Closes a connection to a FEM
        '''
        if self.__class__.connectedFem != None:
            self.__class__.connectedFem.close()
            self.__class__.connectedFem = None
            
    def help_close(self):
        print self.do_close.__doc__
        
    def do_timer(self, s):
        '''
        Enables or disables transaction timer
        Syntax: timer [on|off]
        '''
        
        params=s.split()
        if len(params) <> 1:
            print "*** Invalid number of arguments"
            return
        
        argStr = string.lower(params[0])
        if argStr == 'on':
            self.timerEnabled = True;
            print "Transaction timer enabled"
        elif argStr == 'off':
            self.timerEnabled = False;
            print "Transaction timer disabled"
        else:
            print "Unrecognised parameter: ", argStr
            return
    
    def help_timer(self):
        print self.do_timer.__doc__   
                              
    def do_config(self, s):
        '''
        Read or write FEM configuration block from EEPROM
        Syntax: config [read|write <key=value>, <key=value>]...
        where key value pairs for write can be:
            mac=XX:XX:XX:XX:XX:XX  : update MAC address
            ip=XXX.XXX.XXX.XXX     : update IP address
            mask=XXX.XXX.XXX.XXX   : update netmask
            gw=XXX.XXX.XXX.XXX     : update gateway
            hightemp=X             : update high temperature setpoint
            crittemp=X             : update critical temperature setpoint
            sw=X.Y                 : update software revision number
            hw=X.Y                 : update hardware revision number
            fw=X.Y                 : update firmware revision number
            boardid=X              : upate board ID
            boardtype=X            : update board type
        '''
        params = s.split()
        
        direction = string.lower(params[0])
        
        if direction == 'read':
            
            # Do an EEPROM read
            try:
                femConfig = self.__class__.connectedFem.configRead()
                print "    FEM EEPROM Configuration"
                print "---------------------------------"
                print femConfig
            except:
                print "Can't read EEPROM configuration from FEM"

        elif direction == 'write':
            
            # Do an EEPROM read and load into a config object
            theConfig = self.__class__.connectedFem.configRead()
            
            # Parse argument list and udpdate recognised parameters
            for param in params[1:]:
                
                # Convert to lower case and split on key=value syntax
                param = string.lower(param)
                try:
                    (key, value) = param.split('=')
                except ValueError:
                    print "*** Parameter", param, "not in key=value format"
                    continue
                
                # Parse for recognised keys and update fields in current configuration
                
                if key == 'mac':  #  MAC address
                    try:
                        mac_addr = value.split(':')
                    except ValueError:
                        print '*** MAC address', value, 'has incorrect format'
                        continue
                    if len(mac_addr) != 6:
                        print '*** MAC address', value, 'has incorrect number of octets'
                        continue                    
                    try:
                        theConfig.net_mac = [int(octet, 16) for octet in mac_addr]
                    except ValueError:  
                        print "*** MAC address", value, 'has illegal octet', octet
                         
                elif key == 'ip': # IP address
                    try:
                        net_ip = value.split('.')
                    except ValueError:
                        print "*** IP address", value, 'has incorrect format'
                        continue
                    if len(net_ip) != 4:
                        print "*** IP address", value, "has incorrect number of octets"
                        continue
                    try:
                        theConfig.net_ip = [int(octet) for octet in net_ip]
                    except ValueError:
                        print "*** IP address", value, "has illegal octet", octet

                elif key == 'mask': # Netmask
                    try:
                        net_mask = value.split('.')
                    except ValueError:
                        print "*** Netmask", value, 'has incorrect format'
                        continue
                    if len(net_mask) != 4:
                        print "*** Netmask", value, "has incorrect number of octets"
                        continue
                    try:
                        theConfig.net_mask = [int(octet) for octet in net_mask]
                    except ValueError:
                        print "*** Netmask", value, "has illegal octet", octet
                        
                elif key == 'gw': # Gateway
                    try:
                        net_gw = value.split('.')
                    except ValueError:
                        print "*** Gateway", value, 'has incorrect format'
                        continue
                    if len(net_gw) != 4:
                        print "*** Gateway", value, "has incorrect number of octets"
                        continue
                    try:
                        theConfig.net_gw = [int(octet) for octet in net_gw]
                    except ValueError:
                        print "*** Gateway", value, "has illegal octet", octet

                elif key == 'hightemp': # High temperature setpoint
                    try:
                        theConfig.temp_high = int(value)
                    except ValueError:
                        print "*** High temperature value specified is not integer"

                elif key == 'crittemp': # Critical temperature setpoint
                    try:
                        theConfig.temp_crit = int(value)
                    except ValueError:
                        print "*** Critical temperature value specified is not integer"                        
                        
                elif key == 'sw': # Software revision
                    try:
                        (major, minor) = value.split('.')
                        theConfig.sw_major_version = int(major)
                        theConfig.sw_minor_version = int(minor)
                    except ValueError:
                        print '*** S/W version', value, 'not recognised'
                        
                elif key == 'fw': # Firmware revision
                    try:
                        (major, minor) = value.split('.')
                        theConfig.fw_major_version = int(major)
                        theConfig.fw_minor_version = int(minor)
                    except ValueError:
                        print '*** F/W version', value, 'not recognised'
                        
                elif key == 'hw': # Hardware revision
                    try:
                        (major, minor) = value.split('.')
                        theConfig.hw_major_version = int(major)
                        theConfig.hw_minor_version = int(minor)
                    except ValueError:
                        print '*** H/W version', value, 'not recognised'
                                                  
                elif key == 'boardid': # Board ID
                    try:
                        theConfig.board_id = int(value)
                    except ValueError:
                        print "*** Board ID value specified is not integer"
                        
                elif key == 'boardtype': # Board type
                    try:
                        theConfig.board_type = int(value)
                    except ValueError:
                        print "*** Board type value specified is not integer"
                        
                else: # Unrecognised key
                    print "Key", key, "not recognised"

            # Reset magic word to correct value if necessary
            if theConfig.magicWord != FemConfig.CONFIG_MAGIC_WORD:
                print "WARNING: resetting config magic word to correct value (was 0x%04X, now 0x%04X)" % (theConfig.magicWord, FemConfig.CONFIG_MAGIC_WORD) 
                theConfig.magicWord = FemConfig.CONFIG_MAGIC_WORD
                
            # Write config back to FEM
            try:            
                ack = self.__class__.connectedFem.configWrite(theConfig)
                print "Got ack: ", ['0x{:X}'.format(result) for result in ack]
                
            except FemClientError as e:
                if e.errno == FemClientError.ERRNO_SOCK_CLOSED:
                    print "*** Error, FEM has closed the client connection"
                    self.do_close(None)
                elif e.errno == FemClientError.ERRNO_SOCK_ERROR:
                    print "*** Socket error on FEM connection:", e.msg
                    self.do_close(None)
                else:
                    print "*** FEM Exception:", e, 'errno=', e.errno
       
        
        else:
            print "Unrecognised config direction"
    
    
    def help_config(self):
        print self.do_config.__doc__                          
 
    def do_cmd(self, s):
        '''
        Sends command transaction to FEM
        '''
        params = s.split()
        if len(params) < 1:
            print "*** Invalid number of arguments"
            return
        
        #theCmd = string.upper(params[0])
        try:
            theCmd = int(params[0])
        except ValueError:
            print "*** Cmmand parameter must be integer (for now!)"
            return
        
        try:
            if self.timerEnabled: t0 = time.time()
            ack = self.__class__.connectedFem.commandSend(theCmd)
            if self.timerEnabled: deltaT = time.time() - t0
            #print "Got ack: ", ['0x{:X}'.format(result) for result in ack]  
           
            if self.timerEnabled: print "Transaction took %.3f secs" % deltaT
            
        except FemClientError as e:
            if e.errno == FemClientError.ERRNO_SOCK_CLOSED:
                print "*** Error, FEM has closed the client connection"
                self.do_close(None)
            elif e.errno == FemClientError.ERRNO_SOCK_ERROR:
                print "*** Socket error on FEM connection:", e.msg
                self.do_close(None)
            else:
                print "*** FEM Exception:", e, 'errno=', e.errno

                               
    def help_cmd(self):
        print self.do_cmd.__doc__
        
    def do_acquire(self, s):
        '''
        Sends acquire command to the DMA controller of the FEM
        Syntax: acquire [config <mode> <bufSize> <bufNum> <numAcqs>|start|stop|status] 
        where config params are:
           mode     : normal, burst, rx, tx or upload
           bufSize  : buffer size to set up
           bufNum   : number of buffers to set up (0=maximise in memory)
           numAcqs  : number of images acquisitions to run
           coalesce : number of RXed images to coalesce before TX
           
        N.B. start, stop and status commands require no additional parameters
        '''
        
        params = s.split()
        
        if len(params) < 1:
            print "*** Invalid number of arguments"
            return
        
        # Initialize default parameters
        cmd      = None
        mode     = None
        bufSize  = None
        bufCount = None
        numAcqs  = None
        coalesce = None
        
        acqCommand = string.lower(params[0])
        
        if acqCommand == 'config':
            
            # Need an additional five parameters (mode, size, count, numAcqs, coalesce)          
            if len(params) < 6:
                print "*** Invalid number of arguments for acquire configuration", len(params)
                return
            
            # Set command
            cmd = FemTransaction.CMD_ACQ_CONFIG
            
            # Decode mode parameter string to mode ID
            modeStr = string.upper(params[1])
            if FemShell.acqModeEncoding.has_key(modeStr):
                mode = FemShell.acqModeEncoding[modeStr]
            else:
                print "*** mode parameter not recognized"
                return
            
            # Try to decode buffer size, count and number of acqs from remaining params
            try:
                bufSize  = int(params[2], 0)
                bufCount = int(params[3], 0)
                numAcqs  = int(params[4], 0)
                coalesce = int(params[5], 0)
            except ValueError:
                print "*** buffer size, count, numAcq and coalesce parameters must be integer"
                return
                        
        elif acqCommand == 'start':
            # Set command
            cmd = FemTransaction.CMD_ACQ_START
            
        elif acqCommand == 'stop':
            # Set command
            cmd = FemTransaction.CMD_ACQ_STOP
            
        elif acqCommand == 'status':
            # Set command
            cmd = FemTransaction.CMD_ACQ_STATUS

        else:                
            print "Unrecognised acquire command:", acqCommand
            return
        
        # Send acquire command to the FEM
        if self.__class__.connectedFem == None:
            print "*** Not connected to a FEM"
            return
        try:
            
            ack = self.__class__.connectedFem.acquireSend(cmd, mode, bufSize, bufCount, numAcqs, coalesce)
            
            if acqCommand == 'status':
                
                if ack[0] == 0:
                    
                    status       = ack[1]
                    bufCount     = ack[2]
                    bufSize      = ack[3]
                    bufDirty     = ack[4]
                    readPtr      = ack[5]
                    writePtr     = ack[6]
                    numAcqs      = ack[7]
                    numBds       = ack[8]
                    totalRecvTop = ack[9]
                    totalRecvBot = ack[10]
                    totalSent    = ack[11]
                    totalErrors  = ack[12]
                    
                    if FemShell.acqStatusEncoding.has_key(status):
                        statusStr = FemShell.acqStatusEncoding[status]
                    else:
                        statusStr = 'UNKNOWN STATUS:', status
                        
                    print "    Status          :", statusStr
                    print "    Buffer count    :", hex(ack[2])
                    print "    Buffer size     :", hex(ack[3])
                    print "    Buffer dirty    :", bufDirty
                    print "    Read pointer    :", hex(readPtr)
                    print "    Write pointer   :", hex(writePtr)
                    print "    Number of acqs  :", numAcqs
                    print "    Configured BDs  :", numBds
                    print "    Total recvd top :", totalRecvTop
                    print "    Total recvd bot :", totalRecvBot
                    print "    Total sent      :", totalSent
                    print "    Total errors    :", totalErrors
                    
                else:
                    print "Got bad ACK on acquire status command from FEM:", ack[0]  
            else:
                print "Got ack: ", ['0x{:X}'.format(result) for result in ack]
                
        except FemClientError as e:
            if e.errno == FemClientError.ERRNO_SOCK_CLOSED:
                print "*** Error, FEM has closed the client connection"
                self.do_close(None)
            elif e.errno == FemClientError.ERRNO_SOCK_ERROR:
                print "*** Socket error on FEM connection:", e.msg
                self.do_close(None)
            else:
                print "*** FEM Exception:", e, 'errno=', e.errno
                
            
    def help_acquire(self):
        print self.do_acquire.__doc__
                
if __name__ == "__main__":
    
    import sys

#    interpreter = FemShell()

    if len(sys.argv) > 1:
        if sys.argv[1] == '-f':
            cmdFile = open(sys.argv[2], 'rt')
            try:
                FemShell(stdin=cmdFile).cmdloop()
            finally:
                cmdFile.close()
        else:   
            FemShell().onecmd(' '.join(sys.argv[1:]))
    else:    
        FemShell().cmdloop()
