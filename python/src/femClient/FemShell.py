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

from femClient.FemClient import FemClient
from femApi.femTransaction import FemTransaction

class FemShell(cmd.Cmd,object):
    
    connectedFem = None;
    timerEnabled = False;
    
    busEncoding = { 'EEPROM' : FemTransaction.BUS_EEPROM ,
                    'I2C'    : FemTransaction.BUS_I2C  ,
                    'RAW'    : FemTransaction.BUS_RAW_REG ,
                    'REG'    : FemTransaction.BUS_RAW_REG,
                    'RDMA'   : FemTransaction.BUS_RDMA
                  } 
    
    widthEncoding = { 'BYTE' : FemTransaction.WIDTH_BYTE, 
                      'WORD' : FemTransaction.WIDTH_WORD, 
                      'LONG' : FemTransaction.WIDTH_LONG
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
        
        self.__class__.connectedFem = FemClient((host, port))

    def help_open(self):
        print self.do_open.__doc__
    
    def do_write(self, s):
        '''
        Writes data to a FEM using the command protocol.
        Syntax: write <bus> <width> <addr> <values...> 
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

        if self.timerEnabled: t0 = time.time()        
        ack = self.__class__.connectedFem.write(bus, width, addr, values)
        if self.timerEnabled: deltaT = time.time() - t0
        
        print "Got ack: ", [hex(result) for result in ack]
        if self.timerEnabled: print "Transaction took %.3f secs" % deltaT  
            
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

        if self.timerEnabled: t0 = time.time()
        values = self.__class__.connectedFem.read(bus, width, addr, length)
        if self.timerEnabled: deltaT = time.time() - t0
       
        try: 
            print "Got results:", [hex(result) for result in values]
        except TypeError:
            print "Can't decode results", values
            
        if self.timerEnabled: print "Transaction took %.3f secs" % deltaT  
        
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
