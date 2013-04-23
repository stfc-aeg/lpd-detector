'''
Created on Apr 17, 2013

@author: Tim Nicholls, STFC Application Engineering Group
'''

from xml.etree.ElementInclude import ElementTree
from xml.etree.ElementTree import ParseError

class LpdReadoutConfigError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return self.msg
    
class LpdReadoutConfig():
    
    def __init__(self, xmlObject, fromFile=False):
        
        if fromFile == True:
            self.tree = ElementTree.parse(xmlObject)
            self.root = self.tree.getroot()
        else:
            self.tree = None;
            self.root = ElementTree.fromstring(xmlObject)

        if self.root.tag != 'lpd_readout_config':
            raise LpdReadoutConfigError('Root element is not an LPD configuration tree')
        
    def parameters(self):
        
        for child in self.root:
            
            param = child.tag
            paramType = child.get('type', default="str")
            valStr = child.get('val', default=None)
            
            if valStr == None:
                raise LpdReadoutConfigError("Parameter %s has no value specified" % param)
            try:            
                if paramType == 'int':
                    val = int(valStr, 0)
                elif paramType == 'bool':
                    if valStr == 'True':
                        val = True
                    elif valStr == 'False':
                        val = False
                    else:
                        raise LpdReadoutConfigError("Parameter %s has illegal boolean value %s" % (param, valStr))
                elif paramType == 'str':
                    val = str(valStr)
                else:
                    raise LpdReadoutConfigError("Parameter %s has illegal type %s" % (param, paramType) )
            except ValueError:
                raise LpdReadoutConfigError("Parameter %s with value %s cannot be converted to type %s" % (param, valStr, paramType))

            yield (param, val)
        
import unittest

class LpdReadoutConfigTest(unittest.TestCase):

    def testFileParse(self):    
        basicConfig = LpdReadoutConfig('tests/basicConfig.xml', fromFile=True)
        for (paramName, paramVal) in basicConfig.parameters():
            print paramName, paramVal, type(paramVal)
    
    
if __name__ == '__main__':
    
    unittest.main()
    

    