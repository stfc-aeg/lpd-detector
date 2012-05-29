"""Unit test for SerialPython.py"""

import excaliburPowerGui
from PyQt4 import QtGui#, QtCore
import unittest, sys

# Create object of serialComm class to test its functions
try:
    app = QtGui.QApplication(sys.argv)
    excaliburObj = excaliburPowerGui.ExcaliburPowerGui(app, bUnitTest=True)
except:
    print "error: ", sys.exc_info()[0], sys.exc_info()[1]


class msgPrintBadInput(unittest.TestCase):
    def testArgumentNone(self):
        """ msgPrint() should fail if msg argument is None """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.msgPrint, None)

    def testArgumentInteger(self):
        """ msgPrint() should fail if msg argument is integer """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.msgPrint, 5)

    def testArgumentFloat(self):
        """ msgPrint() should fail if msg argument is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.msgPrint, 3.2)

    def testArgumentBoolean(self):
        """ msgPrint() should fail if msg argument is boolean """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.msgPrint, True)
        
class KnownMsgPrint(unittest.TestCase):
    knownMessage = ( ("Bad", True),
                     ("Error", True),)
    
    def testMsgPrint(self):
        """ msgPrint() should return True if argument is string """
        for errorString, boolean in self.knownMessage:
            result = excaliburObj.msgPrint(errorString)
            self.assertEqual(boolean, result)
        

class logErrorBadInput(unittest.TestCase):
    def testArgumentNone(self):
        """  logError() should fail if msgError argument is None """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.logError, None)

    def testArgumentInteger(self):
        """  logError() should fail if msgError argument is integer """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.logError, 3)

    def testArgumentFloat(self):
        """  logError() should fail if msgError argument is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.logError, 1.2)

    def testArgumentBoolean(self):
        """  logError() should fail if msgError argument is boolean """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.logError, True)

class updatePcf8574DeviceBadInput(unittest.TestCase):
    #def updatePcf8574Device(self, bEnableLvSetting, bEnableBiasSetting):
    def testFirstArgumentNone(self):
        """  updatePcf8574Device() should fail if bEnableLvSetting argument is None """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.updatePcf8574Device, None, True)

    def testFirstArgumentInteger(self):
        """  updatePcf8574Device() should fail if bEnableLvSetting argument is integer """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.updatePcf8574Device, 3, True)

    def testFirstArgumentFloat(self):
        """  updatePcf8574Device() should fail if bEnableLvSetting argument is float """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.updatePcf8574Device, 1.2, True)

    def testFirstArgumentString(self):
        """  updatePcf8574Device() should fail if bEnableLvSetting argument is string """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.updatePcf8574Device, "True", True)


    def testSecondArgumentNone(self):
        """  updatePcf8574Device() should fail if bEnableBiasSetting argument is None """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.updatePcf8574Device, True, None)

    def testSecondArgumentInteger(self):
        """  updatePcf8574Device() should fail if bEnableBiasSetting argument is integer """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.updatePcf8574Device, True, 3)

    def testSecondArgumentFloat(self):
        """  updatePcf8574Device() should fail if bEnableBiasSetting argument is float """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.updatePcf8574Device, True, 1.2)

    def testSecondArgumentString(self):
        """  updatePcf8574Device() should fail if bEnableBiasSetting argument is string """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.updatePcf8574Device, False, "True")

class writePcf8574BadInput(unittest.TestCase):
    #def writePcf8574(self, bEnableLvSetting, bEnableBiasSetting):
    def testArgumentNone(self):
        """  writePcf8574() should fail if bEnableLvSetting argument is None """
        self.assertRaises(excaliburPowerGui.ArgumentTypeNoneError, excaliburObj.writePcf8574, None)

    def testArgumentFloat(self):
        """  writePcf8574() should fail if bEnableLvSetting argument is float """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.writePcf8574, 1.2)

    def testArgumentBoolean(self):
        """  writePcf8574() should fail if bEnableLvSetting argument is boolean """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.writePcf8574, True)


class KnownLogError(unittest.TestCase):
    knownError = ( ("Bad", True),
                   ("Error", True),)
    
    def testLogError(self):
        """ logError() should return True if argument is string """
        for errorString, boolean in self.knownError:
            result = excaliburObj.logError(errorString)
            self.assertEqual(boolean, result)
        

#class KnownLm92ToDegrees(unittest.TestCase):
#    knownValues = ( (4, 0),         # temp_min = -55c, but arduino code starch from 0c
#                    (8, 0.0625),
#                    (16, 0.125),
#                    (32, 0.25),
#                    (64, 0.5),
#                    (128, 1),
#                    (196, 1.5),
#                    (256, 2),
#                    (384, 3),
#                    (512, 4),
#                    (1024, 8),
#                    (2048, 16),
#                    (4096, 32),
#                    (8192, 64),
#                    (9360, 73.125),
#                    (19200, 150),   # temp_max = +150c
#                    )
#
#    def testLm92ToDegrees(self):
#        """lm92ToDegrees() should turn lm92 13 bit format into degrees C"""
#        for lm92Degree, centiDegree in self.knownValues:
#            result = excaliburObj.lm92ToDegrees(lm92Degree)
#            self.assertEqual(centiDegree, result)
#
#
#class lm92ToDegreesBadInput(unittest.TestCase):
#    def testTooLarge(self):
#        """lm92ToDegrees should fail with large input"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.lm92ToDegrees, 19201)
#        
#    def testTooSmall(self):
#        """lm92ToDegrees should fail with too small input"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.lm92ToDegrees, 3)
#        
#    def testZero(self):
#        """lm92ToDegrees should fail with 0 input"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.lm92ToDegrees, 0)
#
#    def testNegative(self):
#        """lm92ToDegrees should fail with negative input"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.lm92ToDegrees, -1)
#        
#        
#class KnownDegreesToLm92(unittest.TestCase):
#    knownValues = ( (0, '0 0'),         # temp_min = -55c, but arduino code start from 0c
#                    (0.125, '0 16'),                    
#                    (0.75, '0 96'),
#                    (0.8125,'0 104'),
#                    (0.875, '0 112'),
#                    (0.9375, '0 120'),
#                    (1, '0 128'),
#                    (1.5, '0 192'),
#                    (3, '1 128'),
#                    (4, '2 0'),
#                    (5, '2 128'),
#                    (7, '3 128'),                    
#                    (9, '4 128'),
#                    (3.125, '1 144'),
#                    (6,'3 0'),
#                    (9.375, '4 176'),
#                    (10.0625, '5 8'),
#                    (12.5, '6 64'),
#                    (15.625, '7 208'),
#                    (18.75, '9 96'),                    
#                    (21.875, '10 240'),
#                    (25.0, '12 128'),
#                    (28.125, '14 16'),
#                    (30.1875, '15 24'),
#                    (31.25, '15 160'),
#                    (34.375, '17 48'),
#                    (40.25, '20 32'),
#                    (50.3125, '25 40'),
#                    (60.375, '30 48'),
#                    (66.4375, '33 56'),
#                    (90.5625, '45 72'),
#                    (100.625, '50 80'),
#                    (110.6875, '55 88'),
#                    (114.75, '57 96'),
#                    (118.125, '59 16'),
#                    (120.5, '60 64'),
#                    (124.875, '62 112'),
#                    (129.25, '64 160'),
#                    (131.625, '65 208'),
#                    (135.0, '67 128'),
#                    (138.375, '69 48'),
#                    (141.75, '70 224'),
#                    (145.125, '72 144'),
#                    (148.5, '74 64'),  
#                    (150, '75 0'),   # temp_max = +150c 
#                    )
#
#
#    def testDegreesToLm92(self):
#        """ degreesToLm92() should turn degrees C into lm92 13 bit format """
#        for centiDegree, lm92Degree in self.knownValues:
#            result = excaliburObj.degreesToLm92(centiDegree)
#            self.assertEqual(lm92Degree, result)
#        
#
#class degreesToLm92BadInput(unittest.TestCase):        
#    def testdegreesToLm92ArgumentTooLarge(self):
#        """degreesToLm92 should fail with large input"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.degreesToLm92, 151)
#
#    def testdegreesToLm92ArgumentNegative(self):
#        """degreesToLm92 should fail with negative input"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.degreesToLm92, -1)
#    def testdegreesToLm92ArgumentNone(self):
#        """ degreesToLm92 should fail with None argument """
#        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.degreesToLm92, None)
#
#    def testdegreesToLm92ArgumentString(self):
#        """ degreesToLm92 should fail with string argument """
#        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.degreesToLm92, "hi")
#
#    def testdegreesToLm92ArgumentBoolean(self):
#        """ degreesToLm92 should fail with boolean argument """
#        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.degreesToLm92, True)
#
#
#class KnownTmpToDegrees(unittest.TestCase):
#    knownValues = ( (8, 0),
#                    (16, 0.0625),
#                    (32, 0.125),
#                    (64, 0.25),
#                    (128, 0.5),
#                    (256, 1),
#                    (512, 2),
#                    (768, 3),
#                    (32512, 127),
#                    )
#
#    def testTmpToDegrees(self):
#        """ tmpToDegrees() should turn degrees C into tmp275 12 bit format """
#        for centiDegree, tmp275Degree in self.knownValues:
#            result = excaliburObj.tmpToDegrees(centiDegree)
#            self.assertEqual(tmp275Degree, result)
#
#
#class tmpToDegreesBadInput(unittest.TestCase):        
#    def testTooLarge(self):
#        """tmpToDegrees should fail with large input"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.tmpToDegrees, 32513)
#
#    def testNegative(self):
#        """tmpToDegrees should fail with negative input"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.tmpToDegrees, -1)


#class writelm92BadInput(unittest.TestCase):
#    def testArgumentMissing(self):
#        """writelm92 should fail if sReg argument not specified, ie NoneType"""
#        self.assertRaises(excaliburPowerGui.ArgumentTypeNoneError, excaliburObj.writelm92, None, None)
#        
#    def testArgumentOneNegative(self):
#        """writelm92 should fail if sReg argument negative"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.writelm92, -1, None)
#        
#    def testArgumentOneTooLarge(self):
#        """writelm92 should fail if sReg argument too large (>7)"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.writelm92, 8, None)
#
#    def testArgumentTwoNegative(self):
#        """writelm92 should fail if sReg argument negative"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.writelm92, 0, -1)
#        
#    def testArgumentTwoTooLarge(self):
#        """writelm92 should fail if sReg argument too large (>7)"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.writelm92, 0, 151)


class readAd7998BadInput(unittest.TestCase):
    def testArgumentNone(self):
        """readAd7998 should fail if address argument is None """
        self.assertRaises(excaliburPowerGui.ArgumentTypeNoneError, excaliburObj.readAd7998, None)

    def testArgumentfloat(self):
        """readAd7998 should fail if address argument is float """
        self.assertRaises(excaliburPowerGui.ArgumentTypeNoneError, excaliburObj.readAd7998,  5.7)

    def testArgumentMissing(self):
        """readAd7998 should fail if address argument not specified """
        self.assertRaises(excaliburPowerGui.ArgumentTypeNoneError, excaliburObj.readAd7998)


class readAd7998_Unit14BadInput(unittest.TestCase):
    def testArgumentOneString(self):
        """readAd7998_Unit14 should fail if ch8to4 argument is string """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit14, "", 0)

    def testArgumentOneNone(self):
        """readAd7998_Unit14 should fail if ch8to4 argument is None """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit14, None, 0)

    def testArgumentOneFloat(self):
        """readAd7998_Unit14 should fail if ch8to4 argument is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit14, 5.9, 0)

    def testArgumentOneBoolean(self):
        """readAd7998_Unit14 should fail if ch8to4 argument is bool """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit14, False, 0)

    def testArgumentTwoString(self):
        """readAd7998_Unit14 should fail if ch8to4 argument is string """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit14, 0, "")

    def testArgumentTwoNone(self):
        """readAd7998_Unit14 should fail if ch8to4 argument is None """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit14, 0, None)

    def testArgumentTwoFloat(self):
        """readAd7998_Unit14 should fail if ch8to4 argument is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit14, 0, 5.9)

    def testArgumentTwoBoolean(self):
        """readAd7998_Unit14 should fail if ch8to4 argument is bool """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit14, 0, False)

    def testArgumentOneTooLarge(self):
        """readAd7998_Unit14 should fail if ch8to4 argument > 8 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit14, 9, 0)

    def testArgumentOneNegative(self):
        """readAd7998_Unit14 should fail if ch8to4 argument < 0 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit14, -1, 0)

    def testArgumentTwoTooLarge(self):
        """readAd7998_Unit14 should fail if ch4to1 argument > 128 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit14, 0, 129)

    def testArgumentTwoNegative(self):
        """readAd7998_Unit14 should fail if ch4to1 argument < 0 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit14, 0, -1)

    def testArgumentTwoBetweenZeroAndSixteen(self):
        """readAd7998_Unit14 should fail if ch4to1 argument between 0 and 16 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit14, 0, 1)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit14, 0, 2)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit14, 0, 4)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit14, 0, 8)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit14, 0, 15)
#            readAd7998_Unit14(ch8to5, ch4to1)
#            valid ranges: 0 <= ch8to5 <= 8, 
#                         0,16 <= ch4to1 <= 128 (i.e. can be 0, or 16-128)
class KnownReadAd7998_Unit14(unittest.TestCase):
    knownChannels =( (0, 16, True),
                     (0, 32, True),
                     (0, 64, True),
                     (0, 128, True),
                     (1, 0, True),
                     (2, 0, True),
                     (4, 0, True),
                     (8, 0, True),
                     )

    def testReadAd7998_Unit14(self):
        """ readAd7998_Unit14 should return True for all values in knownChannels tuple """
        for arg1, arg2, output in self.knownChannels:
            result = excaliburObj.readAd7998_Unit14(arg1, arg2)
            self.assertEqual(output, result)

class readAd7998_Unit15BadInput(unittest.TestCase):
    def testArgumentOneString(self):
        """readAd7998_Unit15 should fail if ch8to4 argument is string """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit15, "", 0)

    def testArgumentOneNone(self):
        """readAd7998_Unit15 should fail if ch8to4 argument is None """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit15, None, 0)

    def testArgumentOneFloat(self):
        """readAd7998_Unit15 should fail if ch8to4 argument is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit15, 5.9, 0)

    def testArgumentOneBoolean(self):
        """readAd7998_Unit15 should fail if ch8to4 argument is bool """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit15, False, 0)

    def testArgumentTwoString(self):
        """readAd7998_Unit15 should fail if ch8to4 argument is string """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit15, 0, "")

    def testArgumentTwoNone(self):
        """readAd7998_Unit15 should fail if ch8to4 argument is None """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit15, 0, None)

    def testArgumentTwoFloat(self):
        """readAd7998_Unit15 should fail if ch8to4 argument is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit15, 0, 5.9)

    def testArgumentTwoBoolean(self):
        """readAd7998_Unit15 should fail if ch8to4 argument is bool """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit15, 0, False)

    def testArgumentOneTooLarge(self):
        """readAd7998_Unit15 should fail if ch8to4 argument > 8 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit15, 9, 0)

    def testArgumentOneNegative(self):
        """readAd7998_Unit15 should fail if ch8to4 argument < 0 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit15, -1, 0)

    def testArgumentTwoTooLarge(self):
        """readAd7998_Unit15 should fail if ch4to1 argument > 128 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit15, 0, 129)

    def testArgumentTwoNegative(self):
        """readAd7998_Unit15 should fail if ch4to1 argument < 0 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit15, 0, -1)

    def testArgumentTwoBetweenZeroAndSixteen(self):
        """readAd7998_Unit15 should fail if ch4to1 argument between 0 and 16 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit15, 0, 1)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit15, 0, 2)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit15, 0, 4)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit15, 0, 8)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit15, 0, 15)
#            readAd7998_Unit15(ch8to5, ch4to1)
#            valid ranges: 0 <= ch8to5 <= 8, 
#                         0,16 <= ch4to1 <= 128 (i.e. can be 0, or 16-128)
class KnownReadAd7998_Unit15(unittest.TestCase):
    knownChannels =( (0, 16, True),
                     (0, 32, True),
                     (0, 64, True),
                     (0, 128, True),
                     (1, 0, True),
                     (2, 0, True),
                     (4, 0, True),
                     (8, 0, True),
                     )

    def testReadAd7998_Unit15(self):
        """ readAd7998_Unit15 should return True for all values in knownChannels tuple """
        for arg1, arg2, output in self.knownChannels:
            result = excaliburObj.readAd7998_Unit15(arg1, arg2)
            self.assertEqual(output, result)

class readAd7998_Unit16BadInput(unittest.TestCase):
    def testArgumentOneString(self):
        """readAd7998_Unit16 should fail if ch8to4 argument is string """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit16, "", 0)

    def testArgumentOneNone(self):
        """readAd7998_Unit16 should fail if ch8to4 argument is None """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit16, None, 0)

    def testArgumentOneFloat(self):
        """readAd7998_Unit16 should fail if ch8to4 argument is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit16, 5.9, 0)

    def testArgumentOneBoolean(self):
        """readAd7998_Unit16 should fail if ch8to4 argument is bool """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit16, False, 0)

    def testArgumentTwoString(self):
        """readAd7998_Unit16 should fail if ch8to4 argument is string """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit16, 0, "")

    def testArgumentTwoNone(self):
        """readAd7998_Unit16 should fail if ch8to4 argument is None """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit16, 0, None)

    def testArgumentTwoFloat(self):
        """readAd7998_Unit16 should fail if ch8to4 argument is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit16, 0, 5.9)

    def testArgumentTwoBoolean(self):
        """readAd7998_Unit16 should fail if ch8to4 argument is bool """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.readAd7998_Unit16, 0, False)

    def testArgumentOneTooLarge(self):
        """readAd7998_Unit16 should fail if ch8to4 argument > 8 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit16, 9, 0)

    def testArgumentOneNegative(self):
        """readAd7998_Unit16 should fail if ch8to4 argument < 0 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit16, -1, 0)

    def testArgumentTwoTooLarge(self):
        """readAd7998_Unit16 should fail if ch4to1 argument > 128 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit16, 0, 129)

    def testArgumentTwoNegative(self):
        """readAd7998_Unit16 should fail if ch4to1 argument < 0 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit16, 0, -1)

    def testArgumentTwoBetweenZeroAndSixteen(self):
        """readAd7998_Unit16 should fail if ch4to1 argument between 0 and 16 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit16, 0, 1)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit16, 0, 2)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit16, 0, 4)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit16, 0, 8)
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.readAd7998_Unit16, 0, 15)
#            readAd7998_Unit16(ch8to5, ch4to1)
#            valid ranges: 0 <= ch8to5 <= 8, 
#                         0,16 <= ch4to1 <= 128 (i.e. can be 0, or 16-128)
class KnownReadAd7998_Unit16(unittest.TestCase):
    knownChannels =( (0, 16, True),
                     (0, 32, True),
                     (0, 64, True),
                     (0, 128, True),
                     (1, 0, True),
                     (2, 0, True),
                     (4, 0, True),
                     (8, 0, True),
                     )

    def testReadAd7998_Unit16(self):
        """ readAd7998_Unit16 should return True for all values in knownChannels tuple """
        for arg1, arg2, output in self.knownChannels:
            result = excaliburObj.readAd7998_Unit16(arg1, arg2)
            self.assertEqual(output, result)


class cmdStringFormat(unittest.TestCase):
    def testFirstCharacter(self):
        """cmdStringFormat argument sCmd's first character must be either of r, R, w, W"""
        self.assertRaises(excaliburPowerGui.MalformedStringError, excaliburObj.cmdStringFormat, "T 35 2 @")

    def testLastCharacter(self):
        """cmdStringFormat argument sCmd's first character must be either of r, R, w, W"""
        self.assertRaises(excaliburPowerGui.MalformedStringError, excaliburObj.cmdStringFormat, "w 35 2 9")

    def testArgumentStringTooShort(self):
        """cmdStringFormat argument sCmd's first character must be either of r, R, w, W"""
        self.assertRaises(excaliburPowerGui.MalformedStringError, excaliburObj.cmdStringFormat, "w 32 @")

    def testArgumentEmptyString(self):
        """ cmdStringFormat should fail if argument is "" """
        self.assertRaises(excaliburPowerGui.MalformedStringError, excaliburObj.cmdStringFormat, "")
        
    def testArgumentSecondCharacter(self):
        """cmdStringFormat argument sCmd's second character and second last character must be space
            i.e. "w 35 2 @" is valid whereas "w35 2 @" and "w 35 2@" are both illegal"""
        self.assertRaises(excaliburPowerGui.MalformedStringError, excaliburObj.cmdStringFormat, "w35 2 @")

    def testArgumentSecondLastCharacter(self):
        """cmdStringFormat argument sCmd's second character and second last character must be space
            i.e. "w 35 2 @" is valid whereas "w35 2 @" and "w 35 2@" are both illegal"""
        self.assertRaises(excaliburPowerGui.MalformedStringError, excaliburObj.cmdStringFormat, "w 35 2@")
    
    def testArgumentCharacterInWrongPlace(self):
        """ cmdStringFormat argument sCmd may only contain none digit character in the first and last
            position of the string, a character anywhere else is illegal"""
        self.assertRaises(excaliburPowerGui.MalformedStringError, excaliburObj.cmdStringFormat, "w 35 x 2 @")
        self.assertRaises(excaliburPowerGui.MalformedStringError, excaliburObj.cmdStringFormat, "w 35 2 l@")
        self.assertRaises(excaliburPowerGui.MalformedStringError, excaliburObj.cmdStringFormat, "w 3e5 2 @")
        self.assertRaises(excaliburPowerGui.MalformedStringError, excaliburObj.cmdStringFormat, "wp 35 2 @")
        
    def testValidArgument_Test1(self):
        """cmdStringFormat works with valid sCmd arguments"""
        self.assertTrue("r 11 1 @")

    def testValidArgument_Test2(self):
        """cmdStringFormat works with valid sCmd arguments"""
        self.assertTrue("R 13 2 @")

    def testValidArgument_Test3(self):
        """cmdStringFormat works with valid sCmd arguments"""
        self.assertTrue("w 14 3 @")

    def testValidArgument_Test4(self):
        """cmdStringFormat works with valid sCmd arguments"""
        self.assertTrue("W 15 4 @")


class testDisplayWarningMessage(unittest.TestCase):
    def testDisplayWarningMessageArgumentInteger(self):
        """ displayWarningMessage() should fail if argument is integer """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.displayWarningMessage, 5)

    def testDisplayWarningMessageArgumentFloat(self):
        """ displayWarningMessage() should fail if argument is float """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.displayWarningMessage, 23.9)

    def testDisplayWarningMessageArgumentBoolean(self):
        """ displayWarningMessage() should fail if argument is boolean """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.displayWarningMessage, True)


class testDisplayErrorMessage(unittest.TestCase):
    def testDisplayErrorMessageArgumentInteger(self):
        """ displayErrorMessage() should fail if argument is integer """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.displayErrorMessage, 5)

    def testDisplayErrorMessageArgumentFloat(self):
        """ displayErrorMessage() should fail if argument is float """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.displayErrorMessage, 23.9)

    def testDisplayErrorMessageArgumentBoolean(self):
        """ displayErrorMessage() should fail if argument is boolean """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.displayErrorMessage, True)

class KnownDisplayErrorMessage(unittest.TestCase):
    knownStrings = ( ("Error", True),
                     ("Test", True),
                     ("Anything", True),
                     )
    def testDisplayErrorMessage(self):
        """ displayErrorMessage should NOT fail if argument IS string """
        for string, test in self.knownStrings:
            result = excaliburObj.displayErrorMessage(string)
            self.assertEqual(test, result)


class KnownScale5V(unittest.TestCase):
    knownValues = ( (0, 0.0),
                    (2, 0.002442002442002442),
                    (2901, 3.542124542124542),
                    (3582, 4.3736263736263732),
                    (4095, 5.0),
                    )

    def testScale5V(self):
        """ scale5V() should scale ad7998's 0-4095 into 0-5V """
        for adcValue, Vscale in self.knownValues:
            result = excaliburObj.scale5V(adcValue)
            self.assertEqual(Vscale, result)


class testScale5VBadInput(unittest.TestCase):
    def testNegative(self):
        """ scale5V() should fail with negative input """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scale5V, -1)
        
    def testTooLarge(self):
        """ scale5V() should fail with too large input """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scale5V, 4096)


class KnownScale1_8V(unittest.TestCase):
    knownValues = ( (0, 0.0),
                    (1, 0.00043956043956043956),
                    (234, 0.10285714285714286),
                    (1625, 0.7142857142857143),
                    (2189, 0.96219780219780215),
                    (3010, 1.323076923076923),
                    (4095, 1.8),
                    )

    def testScale1_8V(self):
        """ scale1_8V() should scale ad7998's 0-4095 into 0-1.8V """
        for adcValue, Vscale in self.knownValues:
            result = excaliburObj.scale1_8V(adcValue)
            self.assertEqual(Vscale, result)


class testScale1_8VBadInput(unittest.TestCase):
    def testNegative(self):
        """ scale1_8V() should fail with negative input """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scale1_8V, -1)

    def testTooLarge(self):
        """ scale1_8V() should fail with too large input """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scale1_8V, 4096)


class KnownScale3_3V(unittest.TestCase):
    knownValues = ( (0, 0.0),
                    (9, 0.010986299999999999),
                    (501, 0.61157069999999991),
                    (1289, 1.5734822999999998),
                    (2070, 2.5268489999999999),
                    (3246, 3.9623921999999996),
                    (4095, 4.9987664999999994),
                    )
    
    def testScale3_3V(self):
        """ scale3_3V() should scale ad7998's 0-4095 into 0-3.3V """
        for adcValue, Vscale in self.knownValues:
            result = excaliburObj.scale3_3V(adcValue)
            self.assertEqual(Vscale, result)
            

class testScale3_3VBadInput(unittest.TestCase):
    def testNegative(self):
        """ scale3_3V() should fail with negative input """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scale3_3V, -1)

    def testTooLarge(self):
        """ scale3_3V() should fail with too large input """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scale3_3V, 4096)

class KnownScale48V(unittest.TestCase):
    knownValues = ( (0, 0.0),
                    (9, 0.10549450549450549),
                    (501,  5.8725274725274721),
                    (1289, 15.109157509157509),
                    (2070, 24.263736263736263),
                    (3246, 38.048351648351648),
                    (4095, 48.0)
                    )
    
    def testScale48V(self):
        """ scale48V() should scale ad7998's 0-4095 into 0-48V """
        for adcValue, Vscale in self.knownValues:
            result = excaliburObj.scale48V(adcValue)
            self.assertEqual(Vscale, result)
            

class testScale48VBadInput(unittest.TestCase):
    def testNegative(self):
        """ scale48V() should fail with negative input """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scale48V, -1)

    def testTooLarge(self):
        """ scale48V() should fail with too large input """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scale48V, 4096)


class KnownScale200V(unittest.TestCase):
    knownValues = ( (0, 0.0),
                    (2, 0.09768009768009768),
                    (9, 0.43956043956043955),
                    (501, 24.468864468864467),
                    (1289, 62.954822954822951),
                    (2070, 101.09890109890109),
                    (3246, 158.53479853479854),
                    (4095, 200.0)
                    )
    
    def testScale200V(self):
        """ scale200V_CurrentlyConversion() should scale ad7998's 0-4095 into 0-200V """
        for adcValue, Vscale in self.knownValues:
            result = excaliburObj.scale200V_CurrentlyConversion(adcValue)
            self.assertEqual(Vscale, result)
            

class testScale200VBadInput(unittest.TestCase):
    def testNegative(self):
        """ scale200V_CurrentlyConversion() should fail with negative input """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scale200V_CurrentlyConversion, -1)

    def testTooLarge(self):
        """ scale200V_CurrentlyConversion() should fail with too large input """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scale200V_CurrentlyConversion, 4096)


class KnownScaleHumidity(unittest.TestCase):
    knownValues = ( (785, 0),
                    (1010, 9),
                    (2135, 54),
                    (3159, 94),
                    (3952, 126),
                    (4095, 132)
                    )
    
    def testScaleHumidity(self):
        """ scaleHumidity() should scale ad7998's 0-4095 into 0-200V """
        for adcValue, Vscale in self.knownValues:
            result = excaliburObj.scaleHumidity(adcValue)
            self.assertEqual(Vscale, result)
            

class testScaleHumidityBadInput(unittest.TestCase):
    def testTooSmall(self):
        """ scaleHumidity() should fail with input < 785 """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scaleHumidity, 784)

    def testTooLarge(self):
        """ scaleHumidity() should fail with too large input """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.scaleHumidity, 4096)


    def testArgumentFloat(self):
        """ scaleHumidity() should fail if msg argument is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.scaleHumidity, 3.2)

    def testArgumentBoolean(self):
        """ scaleHumidity() should fail if msg argument is boolean """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.scaleHumidity, True)

class writead5301_u12(unittest.TestCase):
    def testArgumentMissing(self):
        """writead5301_u12 should fail if decimalBinaryCode argument not specified, ie NoneType"""
        self.assertRaises(excaliburPowerGui.ArgumentTypeNoneError, excaliburObj.writead5301_u12, None)
        
    def testArgumentOneNegative(self):
        """writead5301_u12 should fail if decimalBinaryCode argument negative"""
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.writead5301_u12, -1)
        
    def testArgumentOneTooLarge(self):
        """writead5301_u12 should fail if decimalBinaryCode argument too large (>256) """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.writead5301_u12, 257)

    def testArgumentFloat(self):
        """ writead5301_u12() should fail if decimalBinaryCode argument is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.writead5301_u12, 3.2)

    def testArgumentBoolean(self):
        """ writead5301_u12() should fail if decimalBinaryCode argument is boolean """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.writead5301_u12, True)



class KnownAd5301ToDegrees(unittest.TestCase):
    knownValues = ( (0, "w 12 0 @"),         # min: 0 in, "0" out
                    (100, "w 12 7 240 @"),
                    (200, "w 12 15 240 @"),
#                    (4096, 32),
#                    (8192, 64),
#                    (9360, 73.125),
#                    (19200, 150),           # max: 200 in, "7 240" out 
                    )

    def testAd5301ToDegrees(self):
        """ad5301ToDegrees() should turn ad5301 13 bit format into degrees C"""
        for ad5301Degree, centiDegree in self.knownValues:
            result = excaliburObj.biasLevelToAd5301Conversion(ad5301Degree)
            self.assertEqual(centiDegree, result)


class ad5301ToDegreesBadInput(unittest.TestCase):
#    # Won't fail with too large input as input masked by 4080 (0x0FF0)
#    def testTooLarge(self):
#        """ad5301ToDegrees should fail with large input"""
#        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.biasLevelToAd5301Conversion, 19201)
        
    def testNegative(self):
        """ad5301ToDegrees should fail with negative input"""
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.biasLevelToAd5301Conversion, -1)



class KnownDebugBooleanValues(unittest.TestCase):
    booleanValues = ( (True, True),
                      (False, False),
                      )
    
    def testToggleDebugComponentsBooleanArgument(self):
        """ Ensure toggleDebugComponents() returns True if argument True, and False for False """
        for inputArgument, what in self.booleanValues:
            result = excaliburObj.toggleDebugComponents(inputArgument)
            self.assertEqual(what, result)

class testToggleDebugComponents(unittest.TestCase):
    ''' The functions argument may only be boolean type '''
    def testInteger(self):
        """ toggleDebugComponents() should fail if received argument is an integer """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.toggleDebugComponents, 1)

    def testFloat(self):
        """ toggleDebugComponents() should fail if received argument is a float """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.toggleDebugComponents, 5.2)

    def testString(self):
        """ toggleDebugComponents() should fail if received argument is a string """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.toggleDebugComponents, "Test")


class KnownSelectFileBooleanValues(unittest.TestCase):
    booleanValues = ( (True, True),
                      (False, False),
                      )
    
    def testToggleSelectFileComponentsBooleanArgument(self):
        """ Ensure toggleSelectFileComponents() returns True if argument True, and False for False """
        for inputArgument, what in self.booleanValues:
            result = excaliburObj.toggleSelectFileComponents(inputArgument)
            self.assertEqual(what, result)

class testToggleSelectFileComponents(unittest.TestCase):
    ''' The functions argument may only be boolean type '''
    def testInteger(self):
        """ toggleSelectFileComponents() should fail if received argument is an integer """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.toggleSelectFileComponents, 1)

    def testFloat(self):
        """ toggleSelectFileComponents() should fail if received argument is a float """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.toggleSelectFileComponents, 5.2)

    def testString(self):
        """ toggleSelectFileComponents() should fail if received argument is a string """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.toggleSelectFileComponents, "Test")


#class testToggleVisibleGuiComponents(unittest.TestCase):
#    ''' The functions argument may only be boolean type '''
#    
#    def testtoggleVisibleGuiComponentsBooleanArgument(self):
#        """ Ensure toggleVisibleGuiComponents True if argument's True, and False if False """
#        for inputArgument, what in  KnownDebugBooleanValues.booleanValues:
#            result = excaliburObj.toggleVisibleGuiComponents(inputArgument)
#            self.assertEqual(what, result)
#            
#    def testInteger(self):
#        """ toggleVisibleGuiComponents() should fail if received argument is a integer """
#        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.toggleVisibleGuiComponents, 1)
#
#    def testFloat(self):
#        """ toggleVisibleGuiComponents() should fail if received argument is a float """
#        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.toggleVisibleGuiComponents, 5.2)
#
#    def testString(self):
#        """ toggleVisibleGuiComponents() should fail if received argument is a string"""
#        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburObj.toggleVisibleGuiComponents, "Test")

class testcompareThresholdsBadInput(unittest.TestCase):
    def testMinGreaterThanMax(self):
        """ compareThresholds should fail unless max argument greater than min argument """
        self.assertRaises(excaliburPowerGui.OutOfRangeError, excaliburObj.compareThresholds, 21, 22, 20, 3)

    def testFirstArgumentNotFloat(self):
        """ compareThresholds should fail if argument one is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, 21.1, 10, 32, 3)
        """ compareThresholds should fail if argument one is string """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, "test", 22, 32, 3)
        """ compareThresholds should fail if argument one is boolean """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, True, 22, 32, 3)

    def testSecondArgumentNotInteger(self):
        """ compareThresholds should fail if argument two is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, 21, 22.0, 32, 3)
        """ compareThresholds should fail if argument two is string """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, 21, "test", 32, 3)
        """ compareThresholds should fail if argument two is boolean """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, 21, True, 32, 3)

    def testThirdArgumentNotInteger(self):
        """ compareThresholds should fail if argument three is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, 21, 22, 20.0, 3)
        """ compareThresholds should fail if argument three is string """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, 21, 22, "Test", 3)
        """ compareThresholds should fail if argument three is boolean """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, 21, 22, True, 3)
        
    def testFourthArgumentNotInteger(self):
        """ compareThresholds should fail if argument four is float """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, 21, 22, 32, 3.0)
        """ compareThresholds should fail if argument four is string """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, 21, 22, 32, "Test")
        """ compareThresholds should fail if argument four is boolean """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.compareThresholds, 21, 22, 32, True)


class KnownUpdateHumidityLed(unittest.TestCase):
    kValues = ( (0, True),
                (1, True),
                (2, True),
                )
    def testUpdateHumidityLed(self):
        """ UpdateHumidityLed() should return True for integers range 0-2 """
        for colour, Boolean in self.kValues:
            result = excaliburObj.updateHumidityLed(colour)
            self.assertEqual(Boolean, result)

class testUpdateHumidityLedBadInput(unittest.TestCase):
    def testHumidityInvalidColourArgument(self):
        """ updateHumidityLed should fail unless colour argument either: 0, 1 or 2 (integer)
            Note: colour must be either: 0 (Green), 1 (Amber) or 2 (Red) """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateHumidityLed, -1)
        """ updateHumidityLed should fail unless colour argument either 0, 1, 2 """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateHumidityLed, 1.5)
        """ updateHumidityLed should fail unless colour argument either 0, 1, 2 """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateHumidityLed, 3)

class KnownUpdateAirTempLed(unittest.TestCase):
    kValues = ( (0, True),
                (1, True),
                (2, True),
                )
    def testUpdateAirTempLed(self):
        """ UpdateAirTempLed() should return True for integers range 0-2 """
        for colour, Boolean in self.kValues:
            result = excaliburObj.updateAirTempLed(colour)
            self.assertEqual(Boolean, result)

class testUpdateAirTempLedBadInput(unittest.TestCase):
    def testAirTempInvalidColourArgument(self):
        """ updateAirTempLed should fail unless colour argument either: 0, 1 or 2 (integer)
            Note: colour must be either: 0 (Green), 1 (Amber) or 2 (Red) """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateAirTempLed, -1)
        """ updateAirTempLed should fail unless colour argument either 0, 1, 2 """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateAirTempLed, 1.5)
        """ updateAirTempLed should fail unless colour argument either 0, 1, 2 """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateAirTempLed, 3)

class KnownUpdateCoolantFlowLed(unittest.TestCase):
    kValues = ( (0, True),
                (1, True),
                (2, True),
                )
    def testUpdateCoolantFlowLed(self):
        """ UpdateCoolantFlowLed() should return True for integers range 0-2 """
        for colour, Boolean in self.kValues:
            result = excaliburObj.updateCoolantFlowLed(colour)
            self.assertEqual(Boolean, result)

class testUpdateCoolantFlowLedBadInput(unittest.TestCase):
    def testCoolantFlowInvalidColourArgument(self):
        """ updateCoolantFlowLed should fail unless colour argument either: 0, 1 or 2 (integer)
            Note: colour must be either: 0 (Green), 1 (Amber) or 2 (Red) """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateCoolantFlowLed, -1)
        """ updateCoolantFlowLed should fail unless colour argument either 0, 1, 2 """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateCoolantFlowLed, 1.5)
        """ updateCoolantFlowLed should fail unless colour argument either 0, 1, 2 """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateCoolantFlowLed, 3)

class KnownUpdateCoolantTempLed(unittest.TestCase):
    kValues = ( (0, True),
                (1, True),
                (2, True),
                )
    def testUpdateCoolantTempLed(self):
        """ UpdateCoolantTempLed() should return True for integers range 0-2 """
        for colour, Boolean in self.kValues:
            result = excaliburObj.updateCoolantTempLed(colour)
            self.assertEqual(Boolean, result)

class testUpdateCoolantTempLedBadInput(unittest.TestCase):
    def testCoolantTempInvalidColourArgument(self):
        """ updateCoolantTempLed should fail unless colour argument either: 0, 1 or 2 (integer)
            Note: colour must be either: 0 (Green), 1 (Amber) or 2 (Red) """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateCoolantTempLed, -1)
        """ updateCoolantTempLed should fail unless colour argument either 0, 1, 2 """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateCoolantTempLed, 1.5)
        """ updateCoolantTempLed should fail unless colour argument either 0, 1, 2 """
        self.assertRaises(excaliburPowerGui.BadArgumentError, excaliburObj.updateCoolantTempLed, 3)

class testCompareTypes(unittest.TestCase):
    knownTypes = ( (None, 0),
                   (1, 1),
                   (3.2, 2),
                   ("hi", 3),
                   (True, 4),
                   )
    def testCompareTypes(self):
        """ compareTypes() should return 0, 1, 2, 3, 4 for argument types NoneType, integer, floats, string, boolean """
        for colour, Boolean in self.knownTypes:
            result = excaliburPowerGui.compareTypes(colour)
            self.assertEqual(Boolean, result)

class testRound2Decimals(unittest.TestCase):
    knownDecimals = ( (0.0, "0.00"),
                      (2.1625, "2.16"),
                      (5.175, "5.17"),
                      (8.4375, "8.44"),
                      (13.9499,  "13.95"),
                      )
    def testRound2Decimals(self):
        """ round2Decimals() should pass all pairs in knownDecimals tuple """
        for floatVar, string in self.knownDecimals:
            result = excaliburPowerGui.round2Decimals(floatVar)
            self.assertEqual(string, result)

class testRound2DecimalsBadInput(unittest.TestCase):
    def testRound2DecimalsArgumentNone(self):
        """ round2Decimals() should fail if argument is None """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburPowerGui.round2Decimals, None)

    def testRound2DecimalsArgumentInteger(self):
        """ round2Decimals() should fail if argument is Integer """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburPowerGui.round2Decimals, 5)
        
    def testRound2DecimalsArgumentString(self):
        """ round2Decimals() should fail if argument is string """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburPowerGui.round2Decimals, "SSS")
        
    def testRound2DecimalsArgumentBoolean(self):
        """ round2Decimals() should fail if argument is boolean """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburPowerGui.round2Decimals, True)

class testRound3Decimals(unittest.TestCase):
    """ NOTE: Python rounded numbers according to binary representation,
                therefore 5 is sometimes rounded up, sometimes down """
    knownDecimals = ( (0.0, "0.000"),
                      (2.1625, "2.163"),
                      (5.175, "5.175"),
                      (8.4375, "8.438"),
                      (13.9499,  "13.950"),
                      )
    def testRound3Decimals(self):
        """ round3Decimals() should pass all pairs in knownDecimals tuple """
        for floatVar, string in self.knownDecimals:
            result = excaliburPowerGui.round3Decimals(floatVar)
            self.assertEqual(string, result)

class testRound3DecimalsBadInput(unittest.TestCase):
    
    def testRound3DecimalsArgumentNone(self):
        """ round3Decimals() should fail if argument is None """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburPowerGui.round3Decimals, None)

    def testRound3DecimalsArgumentInteger(self):
        """ round3Decimals() should fail if argument is Integer """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburPowerGui.round3Decimals, 5)
        
    def testRound3DecimalsArgumentString(self):
        """ round3Decimals() should fail if argument is string """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburPowerGui.round3Decimals, "SSS")
        
    def testRound3DecimalsArgumentBoolean(self):
        """ round3Decimals() should fail if argument is boolean """
        self.assertRaises(excaliburPowerGui.WrongVariableType, excaliburPowerGui.round3Decimals, True)


if __name__ == "__main__":
    # Run in all unittests
    unittest.main()
    # Close serial connection after unittests complete
#    excaliburObj.sCom.close()
    
    