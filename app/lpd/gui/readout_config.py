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
            try:
                self.tree = ElementTree.parse(xmlObject)
            except IOError as e:
                raise LpdReadoutConfigError(str(e))
            except ParseError as e:
                raise LpdReadoutConfigError(str(e))
            self.root = self.tree.getroot()
        else:
            self.tree = None;
            try:
                self.root = ElementTree.fromstring(xmlObject)
            except ParseError as e:
                raise LpdReadoutConfigError(str(e))
            
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
                valStr = valStr.split(",")
                valLength = len( valStr)
                val = []

                for idx in range(valLength):

                    if paramType == 'int':
                        val.append( int(valStr[idx], 0))
                    elif paramType == 'bool':
                        if valStr[idx] == 'True':
                            val.append( True)
                        elif valStr[idx] == 'False':
                            val.append( False)
                        else:
                            raise LpdReadoutConfigError("Parameter %s has illegal boolean value %s" % (param, valStr[idx]))
                    elif paramType == 'str':
                        val.append( str(valStr[idx]))
                    else:
                        raise LpdReadoutConfigError("Parameter %s has illegal type %s" % (param, paramType) )

                if valLength == 1:
                    if paramType == 'int':
                        val = val[0]
                    elif paramType == 'bool':
                        val = val[0]
                    elif paramType == 'str':
                        val = val[0]

            except ValueError:
                raise LpdReadoutConfigError("Parameter %s with value %s cannot be converted to type %s" % (param, valStr[idx], paramType))

            yield (param, val)
        
import unittest

class LpdReadoutConfigTest(unittest.TestCase):

    def testFileParse(self):    
        basicConfig = LpdReadoutConfig('tests/basicConfig.xml', fromFile=True)
        for (paramName, paramVal) in basicConfig.parameters():
            print(paramName, paramVal, type(paramVal))
    
    def testIllegalFileParse(self):
        with self.assertRaises(LpdReadoutConfigError):
            LpdReadoutConfig("tests/illegalConfig.xml", fromFile=True)
            
    def testMissingFileParse(self):
        with self.assertRaises(LpdReadoutConfigError):
            LpdReadoutConfig('missingFileName.xml', fromFile=True)
     
    def testStringParse(self):
    
        xmlStr = '''<?xml version="1.0"?>            
                    <lpd_readout_config name="Basic Config">
                        <tenGig0SourceMac type="str" val="62-00-00-00-00-01"/>
                        <tenGig0SourceIp type="str" val="10.0.0.2"/>
                        <tenGig0SourcePort type="int" val="0"/>
                        <tenGig0DestMac type="str" val="00-07-43-10-65-A0"/>
                        <tenGig0DestIp type="str" val="10.0.0.1"/>
                        <tenGig0DestPort type="int" val="61649"/>
                        <femAsicEnableMask type="int" val="9999"/>
                    </lpd_readout_config>    
                  '''
        # Shouldn't raise an exception parsing this file
        LpdReadoutConfig(xmlStr)
        
    def testIllegalStringParse(self):
        
        illegalXmlStr = '''<?xml version="1.0"?>
                           <lpd_readout_config name="Basic Config">
                            This is illegal XML syntax
                        '''
        with self.assertRaises(LpdReadoutConfigError):
            LpdReadoutConfig(illegalXmlStr)
            
if __name__ == '__main__':
    
    unittest.main()
    

    