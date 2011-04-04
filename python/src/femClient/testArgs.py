'''
Created on 30 Mar 2011

@author: tcn
'''

class TestArgs():
    
    def __init__(self, encoded=None, **kwargs):
        print "Encoded", encoded
        for key in kwargs:
            print "Keyword arg: %s = %s" % (key, kwargs[key])
        
        
if __name__ == '__main__':
    
    test1 = TestArgs(1, cmd=2,)
    test2 = TestArgs(cmd="12345")
    
    