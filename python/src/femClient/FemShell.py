'''
Created on 22 Mar 2011

@author: tcn
'''

import cmd
import os
import readline
import string

from femClient.FemClient import FemClient

class FemShell(cmd.Cmd,object):
    
    connectedFem = None;
    
    def __init__(self, completekey='tab', stdin=None, stdout=None, cmdqueue=None):
      
        cmd.Cmd.__init__(self, completekey, stdin, stdout)
        
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
        return True;
    
    def help_exit(self):
        print "Exit the shell (you can also use Ctrl-D)"
        
    do_EOF = do_exit
    help_EOF = help_exit
    do_quit = do_exit
    help_quit = help_exit
    do_end = do_exit
           
    def help_help(self):
        print "Provides help for all commands, or type help <topic> for a specific command"
        
    def do_shell(self, s):
        os.system(s)
        
    def help_shell(self):
        print "Executes system shell command"
        
    def do_for(self, s):

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
        print """
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
"""
    def help_end(self):
        print "Terminates a for loop"
         
    def do_echo(self, s):
        print s
               
    def help_echo(self):
        print "Echoes any output back to user"
           
    def do_open(self, s):
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
        print "Opens a new connection to a FEM."
        print "Syntax: open <addr> <port>" 
    
    def do_write(self, s):
        params = s.split()
        if len(params) < 3:
            print "*** Invalid numnber of arguments"
            return
        try:
            cmd = int(params[0], 0)
            addr = int(params[1], 0)
            values = tuple([int(param, 0) for param in params[2:]])
        except ValueError:
            print "*** parameters must be integer"
            return
            
        self.__class__.connectedFem.write(cmd, addr, values)
    
    def help_write(self):
        print "Writes data to a FEM"
        print "Syntax: write <int1> <int2> <int3> <int4>"
        
    def do_close(self, s):
        self.__class__.connectedFem.close()
        self.__class__.connectedFem = None
            
    def help_close(self):
        print "Closes connection to a FEM"
                              
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
