from __future__ import print_function, division

import sys
if sys.version_info > (3,):
    xrange = range

# Check in setParaValue() for list/integer type 
import os, time

from xml.etree.ElementInclude import ElementTree
from xml.etree.ElementTree import ParseError

# Define Exception Class
class LpdAsicSetupParamsInvalidRangeError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)

class LpdAsicSetupParamsError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)


class LpdAsicSetupParams(object):
 
    # Class Constants
    SEQLENGTH = 123
    # Enumerate the dictionary's indices 
    WIDTH, POSN, VALUES, SKIP, TAGS = range(5)
    
    # xml lookup tables

    biasCtrlLookupTable = [ 24,  19,  44,  39,  14,  34,  29,   9,   4,  23,  18,  13,  43,   8,   3,  22, 
                            17,  12,   7,  38,   2,  33,  28,  21,  42,  37,  32,  27,  41,  16,  36,  11, 
                            31,  46,  30,   5,  26,  45,  40,  35,  25,  20,  15,  10,   6,   1,   0, ]

    
    muxDecoderLookupTable = [511, 479, 447, 415, 383, 351, 319, 287, 255, 223, 191, 159, 127,  95,  63,  31, 
                            510, 478, 446, 414, 382, 350, 318, 286, 254, 222, 190, 158, 126,  94,  62,  30, 
                            509, 477, 445, 413, 381, 349, 317, 285, 253, 221, 189, 157, 125,  93,  61,  29, 
                            508, 476, 444, 412, 380, 348, 316, 284, 252, 220, 188, 156, 124,  92,  60,  28, 
                            507, 475, 443, 411, 379, 347, 315, 283, 251, 219, 187, 155, 123,  91,  59,  27, 
                            506, 474, 442, 410, 378, 346, 314, 282, 250, 218, 186, 154, 122,  90,  58,  26, 
                            505, 473, 441, 409, 377, 345, 313, 281, 249, 217, 185, 153, 121,  89,  57,  25, 
                            504, 472, 440, 408, 376, 344, 312, 280, 248, 216, 184, 152, 120,  88,  56,  24, 
                            503, 471, 439, 407, 375, 343, 311, 279, 247, 215, 183, 151, 119,  87,  55,  23, 
                            502, 470, 438, 406, 374, 342, 310, 278, 246, 214, 182, 150, 118,  86,  54,  22, 
                            501, 469, 437, 405, 373, 341, 309, 277, 245, 213, 181, 149, 117,  85,  53,  21, 
                            500, 468, 436, 404, 372, 340, 308, 276, 244, 212, 180, 148, 116,  84,  52,  20, 
                            499, 467, 435, 403, 371, 339, 307, 275, 243, 211, 179, 147, 115,  83,  51,  19, 
                            498, 466, 434, 402, 370, 338, 306, 274, 242, 210, 178, 146, 114,  82,  50,  18, 
                            497, 465, 433, 401, 369, 337, 305, 273, 241, 209, 177, 145, 113,  81,  49,  17, 
                            496, 464, 432, 400, 368, 336, 304, 272, 240, 208, 176, 144, 112,  80,  48,  16, 
                            495, 463, 431, 399, 367, 335, 303, 271, 239, 207, 175, 143, 111,  79,  47,  15, 
                            494, 462, 430, 398, 366, 334, 302, 270, 238, 206, 174, 142, 110,  78,  46,  14, 
                            493, 461, 429, 397, 365, 333, 301, 269, 237, 205, 173, 141, 109,  77,  45,  13, 
                            492, 460, 428, 396, 364, 332, 300, 268, 236, 204, 172, 140, 108,  76,  44,  12, 
                            491, 459, 427, 395, 363, 331, 299, 267, 235, 203, 171, 139, 107,  75,  43,  11, 
                            490, 458, 426, 394, 362, 330, 298, 266, 234, 202, 170, 138, 106,  74,  42,  10, 
                            489, 457, 425, 393, 361, 329, 297, 265, 233, 201, 169, 137, 105,  73,  41,   9, 
                            488, 456, 424, 392, 360, 328, 296, 264, 232, 200, 168, 136, 104,  72,  40,   8, 
                            487, 455, 423, 391, 359, 327, 295, 263, 231, 199, 167, 135, 103,  71,  39,   7, 
                            486, 454, 422, 390, 358, 326, 294, 262, 230, 198, 166, 134, 102,  70,  38,   6, 
                            485, 453, 421, 389, 357, 325, 293, 261, 229, 197, 165, 133, 101,  69,  37,   5, 
                            484, 452, 420, 388, 356, 324, 292, 260, 228, 196, 164, 132, 100,  68,  36,   4, 
                            483, 451, 419, 387, 355, 323, 291, 259, 227, 195, 163, 131,  99,  67,  35,   3, 
                            482, 450, 418, 386, 354, 322, 290, 258, 226, 194, 162, 130,  98,  66,  34,   2, 
                            481, 449, 417, 385, 353, 321, 289, 257, 225, 193, 161, 129,  97,  65,  33,   1, 
                            480, 448, 416, 384, 352, 320, 288, 256, 224, 192, 160, 128,  96,  64,  32,   0, ]


    pixelSelfTestLookupTable = [511, 510, 509, 508, 507, 506, 505, 504, 503, 502, 501, 500, 499, 498, 497, 496, 
                                480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 
                                479, 478, 477, 476, 475, 474, 473, 472, 471, 470, 469, 468, 467, 466, 465, 464, 
                                448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 
                                447, 446, 445, 444, 443, 442, 441, 440, 439, 438, 437, 436, 435, 434, 433, 432, 
                                416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 
                                415, 414, 413, 412, 411, 410, 409, 408, 407, 406, 405, 404, 403, 402, 401, 400, 
                                384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 
                                383, 382, 381, 380, 379, 378, 377, 376, 375, 374, 373, 372, 371, 370, 369, 368, 
                                352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 
                                351, 350, 349, 348, 347, 346, 345, 344, 343, 342, 341, 340, 339, 338, 337, 336, 
                                320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 
                                319, 318, 317, 316, 315, 314, 313, 312, 311, 310, 309, 308, 307, 306, 305, 304, 
                                288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 
                                287, 286, 285, 284, 283, 282, 281, 280, 279, 278, 277, 276, 275, 274, 273, 272, 
                                256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 
                                255, 254, 253, 252, 251, 250, 249, 248, 247, 246, 245, 244, 243, 242, 241, 240, 
                                224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 
                                223, 222, 221, 220, 219, 218, 217, 216, 215, 214, 213, 212, 211, 210, 209, 208, 
                                192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 
                                191, 190, 189, 188, 187, 186, 185, 184, 183, 182, 181, 180, 179, 178, 177, 176, 
                                160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 
                                159, 158, 157, 156, 155, 154, 153, 152, 151, 150, 149, 148, 147, 146, 145, 144, 
                                128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 
                                127, 126, 125, 124, 123, 122, 121, 120, 119, 118, 117, 116, 115, 114, 113, 112, 
                                 96,  97,  98,  99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 
                                 95,  94,  93,  92,  91,  90,  89,  88,  87,  86,  85,  84,  83,  82,  81,  80, 
                                 64,  65,  66,  67,  68,  69,  70,  71,  72,  73,  74,  75,  76,  77,  78,  79, 
                                 63,  62,  61,  60,  59,  58,  57,  56,  55,  54,  53,  52,  51,  50,  49,  48, 
                                 32,  33,  34,  35,  36,  37,  38,  39,  40,  41,  42,  43,  44,  45,  46,  47, 
                                 31,  30,  29,  28,  27,  26,  25,  24,  23,  22,  21,  20,  19,  18,  17,  16, 
                                  0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,  14,  15, ]


    def __init__(self, xmlObject, pixelFeedbackOverride=-1, pixelSelfTestOverride=-1, loadMode=1, bDebug=False, debugKey="", preambleBit=None, fromFile=False, strict=True):
        # Check that preambleBit argument was supplied
        # Currently (16/01/2013) serial clock must be kept high for six bits
        #    BEFORE the first slow control bit is sent. If these number of bits changes in the future,
        #    then simply modify argument preambleBit accordingly
        if preambleBit == None:
            raise LpdAsicSetupParamsError('Class LpdAsicSetupParams mandatory argument "preambleBit" NOT specified')
        else:
            self.preambleBit = preambleBit

        # load mode (0=parallel, 1=serial)
        self.loadMode = loadMode

        strict = True
        # Set the strict syntax flag to specified value (defaults to true)
        self.strict = strict
        
        ''' Debug info: '''
        self.bDebug = bDebug
        self.debugKey = debugKey
        self.debugKeys = (self.debugKey, self.debugKey+"_default")

        if self.bDebug:
            print("Class arguments: debugKey: ", self.debugKey, " debugKeys: ", self.debugKeys)
            print("FeedbackOverride: %s SelfTestOverride: %s "%  (pixelFeedbackOverride, pixelSelfTestOverride), "preamble: ", preambleBit, "fromFile: ", fromFile, "strict: ", strict)

        self.numTiles         = 16
        self.numAsicsPerTile  = 8
        self.numPixelsPerAsic = 512
        self.numDaqsPerAsic   = 47
        # numTilesToLoad - 1 for parallel, 16 for serial load mode 
        if self.loadMode:   self.numTilesToLoad = self.numTiles
        else:               self.numTilesToLoad = 1
        
        if self.bDebug:
            if self.loadMode:   print("*** Serial (Daisy chain) load mode")
            else:               print("*** Parallel load mode")
        
        #    paramsDict = {'dictKey'                        : [width, posn, values, skip, tags[bPixelTagRequired, bIndexTagRequired, bNestedList]]}
        self.paramsDict = {'mux_decoder_default'            : [3,  -1,     self.perAsicParam(),    0, [False, False, False]],
                           'mux_decoder'                    : [3,  0,      self.perPixelParam(),   0, [True,  False, True]],
                           'feedback_select_default'        : [1,  -1,     self.perAsicParam(),    0, [False, False, False]],
                           'feedback_select'                : [1,  1536,   self.perPixelParam(),   3, [True,  False, True]],
                           'self_test_decoder_default'      : [3,  -1,     self.perAsicParam(),    0, [False, False, False]],
                           'self_test_decoder'              : [3,  1537,   self.perPixelParam(),   1, [True,  False, True]],
                           'self_test_enable'               : [1,  3584,   self.perAsicParam(),    0, [False, False, False]],
                           'daq_bias_default'               : [5,  -1,     self.perAsicParam(),    0, [False, False, False]],
                           'daq_bias'                       : [5,  3585,   self.perDaqParam(),     0, [False, True,  True]],
                           'spare_bits'                     : [5,  3820,   self.perAsicParam(),    0, [False, False, False]],       # Special Case: 5 bits cover everything
                           'filter_control'                 : [20, 3825,   self.perAsicParam(),    0, [False, False, False]],       # Special Case: 20 bits cover everything
                           'adc_clock_delay'                : [20, 3845,   self.perAsicParam(),    0, [False, False, False]],       # Special Case: 20 bits cover everything
                           #'digital_control'                : [40, 3865,   self.perAsicParam(),    0, [False, False, False]],      # Superseded by individual keys
                           # Making (most of) Digital Control keyword accessible
                           'digital_reserved'               : [4, 3865,   self.perAsicParam(),     0, [False, False, False]],
                           'digital_reset3'                 : [7, 3869,   self.perAsicParam(),     0, [False, False, False]],
                           'digital_reset2'                 : [7, 3876,   self.perAsicParam(),     0, [False, False, False]],
                           'digital_reset1'                 : [7, 3883,   self.perAsicParam(),     0, [False, False, False]],
                           'digital_clock_counter_offset'   : [7, 3890,   self.perAsicParam(),     0, [False, False, False]],
                           # Clock Select configurable elsewhere - therefore NOT made accessible here
                           }

        # Variables used to override feedback_select_default, self_test_decoder_default, if different value(s) supplied by setOverrideValues() function
        self.overrideFeedback = pixelFeedbackOverride    # Overrides feedback_select_default
        self.overrideSelfTest = pixelSelfTestOverride    # Overrides self_test_decoder_default

        ''' Debug information '''
        if self.bDebug:
            print("Class LpdAsicSetupParams initialising, reading ")
            if fromFile:
                print("file: ")
            else:
                print("string: ")
            print(xmlObject)
                
        try:
            # Parse the XML specified, either from a file if the fromFile flag
            # was set or from the string passed
            if fromFile == True:
                self.tree = ElementTree.parse(xmlObject)
                self.root = self.tree.getroot()
            else:
                self.tree = None 
                self.root = ElementTree.fromstring(xmlObject)
        except Exception as e:
            raise LpdAsicSetupParamsError('Error parsing XML: %s' % e)
            
        # Get the root of the tree and verify it is an 'lpd_setup_params' element
        if self.root.tag != 'lpd_setup_params':
            raise LpdAsicSetupParamsError('Root element is not an LPD slow control command')

        
    def perAsicParam(self, defaultVal = -1):
        return [[defaultVal for asic in xrange(self.numAsicsPerTile)] for tile in xrange(self.numTiles)]
    
    def perPixelParam(self, defaultVal = -1):
        return [[[defaultVal for pixel in xrange(self.numPixelsPerAsic)] for asic in xrange(self.numAsicsPerTile)] for tile in xrange(self.numTiles)]
    
    def perDaqParam(self, defaultVal = -1):
        return [[[defaultVal for pixel in xrange(self.numDaqsPerAsic)] for asic in xrange(self.numAsicsPerTile)] for tile in xrange(self.numTiles)]


    def getParamValue(self, dictKey, tileNum=None, asicNum=None):
        ''' 
            Obtains the three variables associated with the dictionary key 'dictKey' 
            and returns them as three variables (the third are in some cases a list) 
        '''        
        # Prevent only tileNum but not asicNum defined, or vice versa
        if (tileNum == None and asicNum != None) or (tileNum != None and asicNum == None):
            raise LpdAsicSetupParamsError("Only one of two argument specified! tileNum={0:<}, asicNum={1:<6}".format( tileNum.__repr__(), asicNum.__repr__()) )

        width = 0xdeadbeef
        posn  = 0xDeadBeef
        val   = 0xDeadBeef
        
        # Does dictKey exist in the dictionary?
        if dictKey in self.paramsDict:
            result = self.paramsDict[dictKey]
            width  = result[LpdAsicSetupParams.WIDTH]
            posn   = result[LpdAsicSetupParams.POSN]
            val    = result[LpdAsicSetupParams.VALUES]
            skip   = result[LpdAsicSetupParams.SKIP]
            tags   = result[LpdAsicSetupParams.TAGS]
        else:
            print("\"" + dictKey + "\" doesn't exist.")
        
        if (tileNum==None and asicNum==None):
            return [width, posn, val, skip, tags]
        else:
            return [width, posn, val[tileNum][asicNum], skip, tags]
 
    def setParamValue(self, dictKey, index, value, tile=0, asic=0):
        ''' 
            Updates the dictionary key 'dictKey' with the new value in 'value', 
            overwriting whatever used to be at position 'index'
        '''
        # Does dictKey exist in the dictionary?
        if dictKey in self.paramsDict:
                        
            # Save the current key's values that we (may) want to retain
            currentValue = self.paramsDict[dictKey]

            # Check that the new value is within valid range
            if not (0 <= value <= ( (2**currentValue[LpdAsicSetupParams.WIDTH]) -1) ):
                raise LpdAsicSetupParamsInvalidRangeError("%s's value outside valid range, max: %i received: %i" % (dictKey, 2**currentValue[LpdAsicSetupParams.WIDTH]-1, value) )
            
            else:
                # Is the nested element a list or an integer?
                if isinstance(currentValue[LpdAsicSetupParams.VALUES][tile][asic], list):

                    currentValue[LpdAsicSetupParams.VALUES][tile][asic][index] = value
                    
                elif isinstance(currentValue[LpdAsicSetupParams.VALUES][tile][asic], int):

                    currentValue[LpdAsicSetupParams.VALUES][tile][asic] = value
                else:
                    print("SetParamValue() Error: Key %s is neither a list nor an integer!" % dictKey)
        else:
            print("\"" + dictKey + "\" doesn't exist.")
            
    def encode(self):
        '''
            Encodes the slow control command(s)..
        '''
        
        # Parse the tree, starting at the root element, populating the dictionary
        # self.paramsDict according to the XML tags
        t1= time.time()
        self.parseElement(self.root)

        t2 = time.time()
        # Construct the bitstream based upon all dictionary keys not ending with _default 
        sequence  = self.buildBitstream()
        t3 = time.time()

#        print("parseElement() took ", t2-t1,  " and buildBitstream() took ", t3-t2)
        # Return the command sequence
        return sequence

    def updateDictionary(self, cmd, child):
        '''
            Update dictionary with entry 'cmd' from XM tag 'child'
        '''

        if self.bDebug: print("\nupdateDictionary() %28s" % cmd)
        
        # Get parameter values; Extract required tags
        pmValues = self.getParamValue(cmd)
        (bPixel, bIndex, bNested) = (pmValues[LpdAsicSetupParams.TAGS][0], pmValues[LpdAsicSetupParams.TAGS][1], 
                                             pmValues[LpdAsicSetupParams.TAGS][2])
        
        # Check against key containing illegal attribute(s) (e.g. _default key containing pixel attribute)
        if not bPixel:
            pixel = self.getAttrib(child, 'pixel')
            if pixel != -2: raise LpdAsicSetupParamsError("%s cannot use 'pixel' attribute" % (child.tag))
        if not bIndex:
            index = self.getAttrib(child, 'index')
            if index != -2: raise LpdAsicSetupParamsError("%s cannot use 'index' attribute" % (child.tag))
                        
        # Get value attribute (always present)
        value = self.getAttrib(child, 'value')
        if value == -2: raise LpdAsicSetupParamsError("Unable to find the required 'value' tag for key '%s'!" % cmd)
        
        if self.bDebug: print("value = ", value)

        # Check for (optional) attributes
        tile = self.getAttrib(child, 'tile')
        asic = self.getAttrib(child, 'asic')

        # tagValue = -2 if tag not specified by XML line
        tagValue = -1
        # If pixel tag, obtain pixel value
        if bPixel:
            tagValue = self.getAttrib(child, 'pixel')
            thisIndex = self.doLookupTableCheck(cmd, tagValue)
#            print("** bPixel=%s tagValue = " % bPixel, tagValue)
        else:
            # Not pixel; Is there an index tag?
            if bIndex:
                tagValue = self.getAttrib(child, 'index')
                thisIndex = self.doLookupTableCheck(cmd, tagValue)
#                print("** bIndex=%s tagValue = " % bIndex, tagValue)
            else:
                # Not pixel, index tags
                thisIndex = 0
        
        # Calculate the length of the nested list if nested
        if bNested: numElements = len( pmValues[LpdAsicSetupParams.VALUES][0][0])
        else:       numElements = 1

        bInfo = False
        if self.bDebug: # and (cmd == self.debugKey):
            print("updateD: tile:", tile, "asic: ", asic)
            bInfo = True

        # Update corresponding dictionary key's value(s)
        if tile > -2:
            if asic > -2:
                # tile and asic specified
                if tagValue > -2:
                    # One element within one specified tile's ASIC
                    self.setParamValue(cmd, thisIndex, value, tile, asic)
                    if bInfo:    print("(1 Tile's ASIC) pixel or index")
                else:
                    # All elements within same asic of one tile
                    for element in range(numElements):
                        self.setParamValue(cmd, element, value, tile, asic)
                    if bInfo:    print("(1 Tile's ASIC) All elements")
            else:
                # target all ASICs within same tile
                if tagValue > -2:
                    for asic in range(self.numAsicsPerTile):
                        self.setParamValue(cmd, thisIndex, value, tile, asic)
                    if bInfo:   print("(1Tile,8ASICs) pixel or index")
                else:
                    for asic in range(self.numAsicsPerTile):
                        for element in range(numElements):
                            self.setParamValue(cmd, element, value, tile, asic)
                    if bInfo:    print("(1 Tile's ASIC); numElements: %i, " % numElements, "value = ", value)
        else:
            # tile not specified
            if asic > -2:
                # asic is specified
                if tagValue > -2:
                    # pixel/index specified, target that element in specific asic in all tiles
                    for tile in range( self.numTilesToLoad):
                        self.setParamValue(cmd, thisIndex, value, tile, asic)
                    if bInfo:    print("(16 Tiles, 1 ASIC) pixel or index")
                else:
                    # target all entries within one specific asic for all tiles
                    for tile in range( self.numTilesToLoad):
                        for element in range(numElements):
                            self.setParamValue(cmd, element, value, tile, asic)
                    if bInfo:    print("(16 Tiles, 1 ASIC) all elements")
            else:
                # Neither tile, asic; target all 128 ASICs
                for tile in range(self.numTilesToLoad):
                    for asic in range(self.numAsicsPerTile):
                        # Update specific element or the lot?
                        if tagValue > -2:
                            self.setParamValue(cmd, thisIndex, value, tile, asic)
                        else:
                            for element in range(numElements):
                                self.setParamValue(cmd, element, value, tile, asic)
                if bInfo:
                    if tagValue > -2:   print("(All Tiles & ASICs) pixel or index")
                    else:               print("(All Tiles & ASICs) all elements")
        
    def getAttrib(self, theElement, theAttrib):
        '''
            Returns the value of the theAttrib attribute of the specified element if it exists,
            or a default value of 1 if not. Can also throw an exception if a non-integer
            attribute is detected
        '''
        
        # Get the attribute or a default value of -2 (differentiate from unspecified value which is -1)
        intAttrib = theElement.get(theAttrib, default='-2')
        
        if self.bDebug and (intAttrib != '-2'):
            print("attrib: '" + theAttrib + "': %15s" % intAttrib + ".")

        # Convert count to integer or raise an exception if this failed
        try:
            attrib = int(intAttrib)
        except ValueError:
            raise LpdAsicSetupParamsError('Non-integer attribute specified')
        
        # Return integer attrib value    
        return attrib

    def doLookupTableCheck(self, dictKey, idx):
        '''
            Accepts the dictionary key 'dictKey' and associated index 'idx' and performs the dictionary lookup for the four different keys that have a dictionary lookup table.
            
            'idx' returned unchanged for the other keys.
        '''

        # Does dictKey have an associated lookup table?
        if dictKey == "mux_decoder":            return LpdAsicSetupParams.muxDecoderLookupTable[idx]
        elif dictKey == "feedback_select":      return LpdAsicSetupParams.pixelSelfTestLookupTable[idx]
        elif dictKey == "self_test_decoder":    return LpdAsicSetupParams.pixelSelfTestLookupTable[idx]
        elif dictKey == "daq_bias":             return LpdAsicSetupParams.biasCtrlLookupTable[idx]
        else:                                   return idx             
        
    def parseElement(self, theElement):
        '''
            Parses an element (partial tree) of the XML command sequence, encoding commands
            into the appropriate values and returning them. Note that slow control is more complicated
            because each parameter is inserted into the slow control bitstream according to its relative position.
            
            NOTE: pixels run 1-512, index 1-47 but to match Python's lists they're numbered 0-511, 0-46.
        '''
        
        if self.bDebug: print("############################################ parseElement() ############################################")

        # The structure of the parameters dictionary:
        # paramsDict = {'dictKey' : [width, posn, value(s), [bPixelTagRequired, bValueTagRequired, bIndexTagRequired]]}
        #     where values(s) is an integer or a list, and the nested list of booleans defines which tags that are required

        # Loop over child nodes of the current element
        for child in theElement:

            # Get the command name (tag) for the current element
            cmd = child.tag
                         
            # Check this command is in the syntax dictionary and process
            # accordingly. Raise an exception if the command is not recognised and
            # strict syntax checking is enabled
            if cmd in self.paramsDict:
                
                self.updateDictionary(cmd, child)
                
            else:
                if self.strict: raise LpdAsicSetupParamsError('Illegal command %s specified' % (child.tag))
        
        if self.bDebug: print("\n\n~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~ check _default ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~")

        # Pass through XXX_default keys and change their value from -1 to 0 unless already set
        for key in self.paramsDict:

            if key.endswith("_default"):
                
                if self.bDebug and (key in self.debugKeys): print("1st Pass:  _default key: %28s" % key, " = \n", self.getParamValue(key))

                # Use overrides if set by API
                if key == 'feedback_select_default':
                    if self.overrideFeedback > -1: 
                        for tile in range(self.numTilesToLoad):
                            for asic in range(self.numAsicsPerTile):
                                self.setParamValue(key, 0, self.overrideFeedback, tile, asic)

                if key == 'self_test_decoder_default':
                    if self.overrideSelfTest > -1:
                        for tile in range(self.numTilesToLoad):
                            for asic in range(self.numAsicsPerTile):
                                self.setParamValue(key, 0, self.overrideSelfTest, tile, asic)

                if self.bDebug and (key in self.debugKeys): print("After overrides:\n", self.getParamValue(key))

                for tile in range(self.numTilesToLoad):
                    for asic in range(self.numAsicsPerTile):
                        # Obtain _default's value
                        defaultKeyValue = self.getParamValue(key, tile, asic)

                        # Is XXX_default's value not specified ?
                        if defaultKeyValue[LpdAsicSetupParams.VALUES] == -1:
                            # Default not set; set it to 0
                            self.setParamValue(key, 0, 0, tile, asic)
                    
                if self.bDebug and (key in self.debugKeys): print("After zeroing -1's:\n", self.getParamValue(key))

        if self.bDebug: print("\n- - - - - - - - - - - - - - - - - - - - - update using _default  - - - - - - - - - - - - - - - - - - - -")
        
        # Check _default keys and update the corresponding keys unless where the associated keys have explicitly set value(s)
        #    e.g. if daq_bias_default = 4 then all values of daq_bias will become 4 (unless set explicitly)

        for key in self.paramsDict:

            if key.endswith("_default"):

                # Obtain key value
                defaultKeyValue = self.getParamValue(key)
                                
                # Derive corresponding key's name
                #    e.g. key = "mux_decoder_default"; sectionKey = "mux_decoder"
                sectionKey = key.replace("_default", "")
                sectionKeyValue = self.getParamValue(sectionKey)
                sectionNumElements = len(sectionKeyValue[LpdAsicSetupParams.VALUES][0][0])

                if self.bDebug and (key in self.debugKeys): print("Compare: '%s' value:\n" % key, defaultKeyValue[LpdAsicSetupParams.VALUES], "\n")

                # All key values not explicitly set: Update using default's value
                for tile in range(self.numTilesToLoad):
                    for asic in range( self.numAsicsPerTile):                
                        for element in range(sectionNumElements):

                            if sectionKeyValue[LpdAsicSetupParams.VALUES][tile][asic][element] == -1:
                                self.setParamValue(sectionKey, element, defaultKeyValue[LpdAsicSetupParams.VALUES][tile][asic], tile, asic)
                                                
                if self.bDebug and (key in self.debugKeys): print("Compare: '%s' value:\n" % sectionKey, sectionKeyValue[LpdAsicSetupParams.VALUES][0][0], "\n")
        
        # Check keys that doesn't end in _default and set any remaining -1 value(s) to 0
        for key in self.paramsDict:

            if key.endswith("_default") is False:
                # All keys that does not end with "_default", and that does not contain a list of values
                #    eg:     self_test_enable, spare_bits, filter_control, adc_clock_delay, digital_reserved, digital_reset3,
                #             .., digital_clock_counter_offset
                
                keyValue = self.getParamValue(key)

                if isinstance(keyValue[LpdAsicSetupParams.VALUES][0][0], int):
                                            
                    if self.bDebug and (key in self.debugKeys): print("2nd Pass: Found integer type: %21s" % key)
                    
                    # Has the value been set already?
                    for tile in range(self.numTilesToLoad):
                        for asic in range(self.numAsicsPerTile):
                            if keyValue[LpdAsicSetupParams.VALUES][tile][asic] == -1:
                                # Not set; Set it to 0
                                self.setParamValue(key, 0, 0, tile, asic)
                else:
                    numElements = len( keyValue[LpdAsicSetupParams.VALUES][0][0])

                    # Has the value been set already?
                    for tile in range(self.numTilesToLoad):
                        for asic in range(self.numAsicsPerTile):
                            for index in range( numElements):
                                if keyValue[LpdAsicSetupParams.VALUES][tile][asic][index] == -1:
                                    # Not set; Set it to 0
                                    self.setParamValue(key, index, 0, tile, asic)
                                    print("***")
     
    def buildBitstream(self):
        '''
            Loop over dictionary keys and building the word bitstream programmatically
        '''
        
        encodedSequence = [[0 for sequence in xrange(LpdAsicSetupParams.SEQLENGTH)] for totalAsics in xrange(self.numTilesToLoad * self.numAsicsPerTile)]

        # Loop over tiles and ASICs
        for tile in range(self.numTilesToLoad):
            for asic in range(self.numAsicsPerTile):

                # Create a bit array to save all the slow control words, bit by bit
                bitwiseArray = [0] * (3905 + self.preambleBit)

                # Loop over dictionary entries 
                for dictKey in self.paramsDict:
        
                    if dictKey.endswith("_default"):
                        continue
                    else:
                        # Get dictionary values for this key
                        cmdParams = self.getParamValue(dictKey)
                        # Word width (number of bits) of this key?
                        keyWidth = cmdParams[LpdAsicSetupParams.WIDTH]
                        # Where does current key reside within the sequence?
                        wordPosition = (cmdParams[LpdAsicSetupParams.POSN] + self.preambleBit) // 32
                        # Slow Control Value(s)
                        slowControlWordContent = cmdParams[LpdAsicSetupParams.VALUES]
        
                        # bitPosition tracks the current bit position relative to the entire length of sequence (0 - 3904)
                        bitPosition = (cmdParams[LpdAsicSetupParams.POSN] + self.preambleBit)
                        
                        #TODO: set preambleBit to 0 (self.preambleBit - self.preambleBit) unless it's that specific ASIC within the very first tile?
                        
                        # Skip - distance between two slow control words within the same section
                        wordSkip = cmdParams[LpdAsicSetupParams.SKIP]

                        if isinstance(slowControlWordContent[tile][asic], list):
                            
                            # Determine number of entries in the nested list
                            numElements = len(slowControlWordContent[tile][asic])

                            # Loop over all the elements of the nested list and produce bitwiseArray (MSB first)
                            #    e.g.: if keyWidth = 3, list = [1, 3, 6, .] then bitwiseOffset = [ (0, 0, 1,) (0, 1, 1,) (1, 1, 0,) ..]
                            for idx in range(numElements):
                                
                                    
                                bitMask = 2**(keyWidth-1)
                                # Iterate over each slow control word for the current key
                                for bitIdx in range(keyWidth):

                                    try:
                                        # bitShiftOffset determines number of bits to shift within current slow control word
                                        bitShiftOffset = (keyWidth-1) - bitIdx

                                        bitwiseArray[bitPosition + keyWidth*idx + bitIdx + wordSkip*idx] = ( (slowControlWordContent[tile][asic][idx] & bitMask) >> bitShiftOffset)
                                        bitMask = bitMask >> 1
                                    
                                    except Exception as e:
                                        self.debugFunction(headerLabel="buildBitstream '%s' error: \"%s\".  " % (dictKey, e), 
                                                           bitPosition=bitPosition, keyWidth=keyWidth, idx1=idx, bitIdx=bitIdx, wordSkip=wordSkip, idx2=idx, 
                                                           tile=tile, asic=asic, idx3=idx, bitMask=bitMask, bitShiftOffset=bitShiftOffset)
                        else:

                            # Do not process empty slow control word(s)
                            if slowControlWordContent[tile][asic] == 0:
                                continue
        
                            # How many bits to use
                            numElements = cmdParams[LpdAsicSetupParams.WIDTH]

                            bitMask = 2**(keyWidth-1)
                            # Loop over all the bits in the slow control word
                            for idx in range(numElements):
                                
                                # bitShiftOffset determines number of bits to shift within current slow control word (from MSB to LSB)
                                bitShiftOffset = (keyWidth-1) - idx
                                try:
                                    bitwiseArray[bitPosition + idx + wordSkip*idx] = ( (slowControlWordContent[tile][asic] & bitMask) >> bitShiftOffset)
                                    bitMask = bitMask >> 1
                                except Exception as e:
                                    
                                    print("key: %s. integer type, Error: %s\n" % (dictKey, e))

                                    try:
                                        bitwiseArray[bitPosition + idx + wordSkip*idx] 
                                    except Exception as e:
                                        print("bitwiseArray is the error source:")
                                        print("bitwiseArray[bp:%4i + i:%3i + wS:%3i * i:%3i] " % (bitPosition, idx, wordSkip, idx))
                                        print(" ==>> [%5i] " % (bitPosition + idx + wordSkip*idx))
                                        raise Exception
                                    try:
                                        (slowControlWordContent[tile][asic]& bitMask) >> bitShiftOffset
                                    except Exception as e:
                                        print("slowControlWordContent is the error source:")
                                        print("slowControlWordContent[t:%2i][a:%1i] & %2i >> %3i "% (tile, asic, bitMask, bitShiftOffset))
                                        raise Exception

                ''' Produce encoded sequence '''

                # Loop over the bitwiseArray and copy 32 bits at a time into the encoded sequence
                for idx in range( len(bitwiseArray) ):

                    # Determine location inside sequence; Determine relative position within current index
                    wordPosition = idx // 32
                    bitOffset = idx % 32

                    # Add running total to sequence; increment bitPosition and check wordPosition 
                    try:
                        encodedSequence[tile*self.numAsicsPerTile + asic][wordPosition] = encodedSequence[tile*self.numAsicsPerTile + asic][wordPosition] | (bitwiseArray[idx] << bitOffset)
                    except Exception as e:
                        print("Key '%s' Error: \"%s\"\n   wordPosition = %i, idx = %i, bitwise sum = %i\n" % (dictKey, e, wordPosition, idx, (bitwiseArray[idx] << bitOffset)))
                        return
                                
        # Return the encoded sequence for this (partial) tree
        return encodedSequence
         
    def generateBitMask(self, numBits):
        '''
            Generates that bit mask to cover the number of bits supplied.
            
            I.e. numBits = 1; returns 1,    2 = > 3, 3 => 7, 4 = > 15
        '''
        theSum = 0
        for idx in range(numBits):
            theSum = theSum | (1 << idx)
        return theSum
    
    def displayDictionaryValues(self):
        '''
            Debug function, used to display the dictionary values
        '''
        elementsToDisplay = 25
        if self.bDebug:
            print("\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- displayDictValues -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
            for cmd in self.paramsDict:
                # Get dictionary key's values
                dictKey = self.getParamValue(cmd)
                
                print("dictKey: %28s" % cmd, " pos'n:  %4i" % dictKey[LpdAsicSetupParams.POSN], "\t [", end="")
                # Is the third variable a list or an integer?
                if isinstance(dictKey[LpdAsicSetupParams.VALUES][0][0], list):
                    
                    numElements = len( dictKey[LpdAsicSetupParams.VALUES][0][0])
                    for idx in range(numElements):
                        if (idx < elementsToDisplay):
                            # Print the first few values
                            print(dictKey[LpdAsicSetupParams.VALUES][0][0][idx], end="")
                        elif idx == elementsToDisplay:
                            print(", .., ", end="")
                        elif idx < (numElements - elementsToDisplay):
                            continue
                        else:
                            # Print the last few values
                            print(dictKey[LpdAsicSetupParams.VALUES][0][0][-1*(numElements-idx)], end="")
    
                elif isinstance(dictKey[LpdAsicSetupParams.VALUES][0][0], int):

                    print(dictKey[LpdAsicSetupParams.VALUES][0][0], end="")
                else:
                    print("displayDictionaryValues() Error: dictKey[LpdAsicSetupParams.VALUES][0][0] is neither a list nor an integer!")
    
                print("]")

    def fetchParamsDictionary(self):
        '''
            Utility function used by unit testing class to obtain dictionary values
        '''
        return self.paramsDict
    
    def debugFunction(self, headerLabel, **kwargs):
        '''
            a debug function that will print a header consisting of the argument(s) provided to the function,
            followed by the value each argument(s)
        '''
        if hasattr(self, 'debugHeaderDict'):
            # Dictionary already exists; check if function called with these variables before
            if self.debugHeaderDict.has_key(headerLabel):
                #function called with this augment list before
                self.debugHeaderDict[headerLabel] += 1
            else:
                #function not called with these arguments before; Add label to dictionary and print header
                self.debugHeaderDict[headerLabel] = 0
        else:
#            print("debugFunction has not a header dictionary")
            self.debugHeaderDict = {}
            self.debugHeaderDict[headerLabel] = 0

        print("*** ", kwargs)
#        if self.debugHeaderDict[headerLabel] == 0:
#            print(headerLabel)
#            for key, value in kwargs.items():
#                print("%s  " % key)
#            print()
#        print(headerLabel)
#        for key, value in kwargs.items():
#            print("%s  " % value)
#        print()

import unittest
    
class LpdAsicSetupParamsTest(unittest.TestCase):
    '''
    Unit test class for LpdAsicSetupParams.
    '''

    # Enumerate load mode options
    PARALLEL, SERIAL = range(2)
    
    bToggle = True #False
    if bToggle:
        def testStringParse(self):
            '''
                Tests that updating a parameter works as expected
            '''
            selfTestPixelIndex = 1
            daqBiasIdx47Value = 11
            daqBiasDefault = 31
            selfTestDecoderDefault = 7
            spareBitsValue = 18
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="TestString">
                                    <self_test_decoder pixel="%i" value="5"/>
                                    <self_test_decoder_default value="%i"/>
                                    <mux_decoder pixel="2" value="0"/>
                                    <mux_decoder_default value="3"/>

                                    <daq_bias index="46" value="%i"/>
                                    <daq_bias_default value="%i"/>
                                    <daq_bias index="2" value="0"/>
                                    
                                    <spare_bits value="%i"/>
                                </lpd_setup_params>
            ''' % (selfTestPixelIndex, selfTestDecoderDefault, daqBiasIdx47Value, daqBiasDefault, spareBitsValue)
    
            bDebug = False
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, 
                                           #bDebug=True, debugKey="daq_bias",
                                           loadMode=LpdAsicSetupParamsTest.PARALLEL)
            paramsObj.encode()
            
            # Display an excerp of each dictionary key's value:
            paramsObj.displayDictionaryValues()
      
            # Setup and compare the unit tests..        
            dictKey = "self_test_decoder_default"
            
            # Expected encoded values
            expectedVals = paramsObj.fetchParamsDictionary()['self_test_decoder_default']
            # The actual values
            selfTestDecoderDefaultVals = paramsObj.getParamValue(dictKey)
    
            if bDebug: print("selfTestDecoderDefaultVals:\n", selfTestDecoderDefaultVals[2][0], "expectedVals:\n", expectedVals[2][0])
            self.assertEqual(selfTestDecoderDefaultVals[2][0], expectedVals[2][0], 'testStringParse() failed to update key \"%s\" as expected' % dictKey)
            
            dictKey = 'self_test_decoder'
            index = selfTestPixelIndex
            value = 5
            
            expectedVals = [3, 1537, [selfTestDecoderDefault] * 512, 1, [True, True, False]]
            expectedVals[2][ LpdAsicSetupParams.pixelSelfTestLookupTable[index] ] = value
    
            self_test_decoderVals = paramsObj.getParamValue(dictKey)
            
            if bDebug: print("Encoded: \n", self_test_decoderVals[2][0][0], "Expected: \n", expectedVals[2])
            self.assertEqual(self_test_decoderVals[2][0][0], expectedVals[2], 'testStringParse() failed to update key \"%s\" as expected' % dictKey)

            dictKey = "daq_bias_default"
            index = 0
            value = daqBiasDefault
            
            expectedVals = [5, -1, [value]*8, 0, [False, True, False]]
            
            daqBiasDefaultVals = paramsObj.getParamValue(dictKey)
            
            if bDebug: print("Encoded: \n", daqBiasDefaultVals[2][0], "Expected: \n", expectedVals[2])
            self.assertEqual(daqBiasDefaultVals[2][0], expectedVals[2], 'testStringParse() failed to update key \"%s\" as expected' % dictKey)
            
            dictKey = 'daq_bias'
            value = daqBiasIdx47Value
            
            expectedVals = [5, 3585, [daqBiasDefault] * 47, 0, [False, True, True]]
    
            expectedVals[2][ LpdAsicSetupParams.biasCtrlLookupTable[2] ] = 0
            expectedVals[2][ LpdAsicSetupParams.biasCtrlLookupTable[46] ] = value
            
            daq_biasVals = paramsObj.getParamValue(dictKey)
    
            if bDebug: print("\nEnc: ", daq_biasVals[2][0][0], "\nExp: ", expectedVals[2])
            self.assertEqual(daq_biasVals[2][0][0], expectedVals[2], 'testStringParse() failed to update key \"%s\" as expected' % dictKey)
    

        def testOutOfRangeKeyValueFails(self):
            '''
                Tests that updating a parameter will fail if value exceeds valid range
            '''
            # Strictly not necessary except for the class constructor requiring a XML file or string
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testOutOfRangeKeyValueFails">
                                    <self_test_decoder_default value="7"/>
                                </lpd_setup_params>
            '''        
            # setParamValue(dictKey, index, value)
            dictKey = "self_test_decoder_default"
            index = 0
            value = 8
        
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, 
                                           #bDebug=True,
                                           loadMode=LpdAsicSetupParamsTest.PARALLEL)

            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
    
            dictKey = "self_test_decoder"
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
    
            dictKey = "mux_decoder_default"
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
    
            dictKey = "mux_decoder"
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
            
            # Test 1 bit widths
            dictKey = "feedback_select_default"
            value = 2
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
    
            dictKey = "feedback_select"
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
    
            dictKey = "self_test_enable"
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
    
            # Test 5 bit widths
            dictKey = "daq_bias_default"
            value = 32
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
    
            dictKey = "daq_bias"
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
    
            dictKey = "spare_bits"
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
    
            # Test 20 bit width
            dictKey = "filter_control"
            value = 1048575+1
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
            
            dictKey = "adc_clock_delay"
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
    
            # Test 4 bit width
            dictKey = "digital_reserved"
            value = 2**4
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
        
            # Test 7 bit width
            dictKey = "digital_reset3"
            value = 2**7
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)
        
            # Test 7 bit width
            dictKey = "digital_reset2"
            value = 2**7
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)

            # Test 7 bit width
            dictKey = "digital_reset1"
            value = 2**7
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)

            # Test 7 bit width
            dictKey = "digital_clock_counter_offset"
            value = 2**7
            with self.assertRaises(LpdAsicSetupParamsInvalidRangeError):
                paramsObj.setParamValue(dictKey, index, value)

        def testInvalidAttributeFails(self):
            '''
                Tests that providing a tag with an attribute that isn't required will raise an exception
            '''
    
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testInvalidAttributeFails1">
                                    <self_test_decoder_default pixel="5" value="7"/>
                                </lpd_setup_params>
            '''
        
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            self.assertRaises(LpdAsicSetupParamsError, paramsObj.encode)
    
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testInvalidAttributeFails2">
                                    <daq_bias pixel="5" value="7"/>
                                </lpd_setup_params>
            '''
        
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            self.assertRaises(LpdAsicSetupParamsError, paramsObj.encode)
    
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testInvalidAttributeFails3">
                                    <daq_bias_default index="15" value="31"/>
                                </lpd_setup_params>
            '''
        
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            self.assertRaises(LpdAsicSetupParamsError, paramsObj.encode)
        
            
        def testSelfTestDecoderDefaultSetValueSeven(self):
            '''
                Test that the key self_test_decoder_default works
            '''
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testSelfTestDecoderDefaultSetValueSeven">
                                    <self_test_decoder_default value="7"/>
                                </lpd_setup_params>
            '''
        
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, 
                                           #bDebug=True, debugKey="self_test_decoder",
                                           loadMode=LpdAsicSetupParamsTest.PARALLEL)
            encodedSequence = paramsObj.encode()

            # Display an excerp of each dictionary key's value:
            paramsObj.displayDictionaryValues()        
    
            # Construct a list of how sequence should look like
            expectedSequence = [0] * LpdAsicSetupParams.SEQLENGTH
    
            for idx in range(48,112):
                expectedSequence[idx] = 0xEEEEEEEE
    
            # Bit shift expected sequence by 6 bits
            expectedSequence = self.bitshiftSlowControlArray(expectedSequence, 6)
    
            # Toggle display of debug information
            if False:
                self.furtherInformation('testSelfTestDecoderDefaultSetValueSeven()', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testSelfTestDecoderDefaultSetValueSeven() failed !')
            
        def testFeedbackSelectDefaultSetValueOne(self):
            '''
                Test that the key feedback_select_default works
            '''
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testFeedbackSelectDefaultSetValueOne">
                                    <feedback_select_default value="1"/>
                                </lpd_setup_params>
            '''
        
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, 
                                           #bDebug=True, debugKey="feedback_select",
                                           loadMode=LpdAsicSetupParamsTest.PARALLEL)
            encodedSequence = paramsObj.encode()
    
            # How the sequence should end up looking
            expectedSequence = [0] * LpdAsicSetupParams.SEQLENGTH
    
            for idx in range(48,112):
                expectedSequence[idx] = 0x11111111
            
            # Bit shift expected sequence by 6 bits
            expectedSequence = self.bitshiftSlowControlArray(expectedSequence, 6)
    
            # Toggle display debug information
            if False:
                self.furtherInformation('testFeedbackSelectDefaultSetValueOne()', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testFeedbackSelectDefaultSetValueOne() failed !')
            
        def testFeedbackSelectAndSelfTestDecoderDefaultsCombined(self):
            '''
                Test that the keys feedback_select_default and self_test_decoder_default work together
            '''
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testFeedbackSelectAndSelfTestDecoderDefaultsCombined">
                                    <feedback_select_default value="1"/>
                                    <self_test_decoder_default value="2"/>
                                </lpd_setup_params>
            '''
        
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            encodedSequence = paramsObj.encode()
    
            # How the sequence should end up looking
            expectedSequence = [0] * LpdAsicSetupParams.SEQLENGTH
    
            for idx in range(48,112):
                expectedSequence[idx] = 0x55555555
    
            # Bit shift expected sequence by 6 bits
            expectedSequence = self.bitshiftSlowControlArray(expectedSequence, 6)
            
            # Toggle display debug information
            if False:
                self.furtherInformation('testFeedbackSelectAndSelfTestDecoderDefaultsCombined()', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testFeedbackSelectAndSelfTestDecoderDefaultsCombined() failed !')
    
        def testMuxDecoderDefault(self):
            '''
                Test that the key mux_decoder_default works
            '''
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testMuxDecoderDefault">
                                    <mux_decoder_default value="5"/>
                                </lpd_setup_params>
            '''
        
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            encodedSequence = paramsObj.encode()
    
            # How the sequence should end up looking
            expectedSequence = [0] * LpdAsicSetupParams.SEQLENGTH
    
            for idx in range(48):
                indexNo = idx % 3
                if indexNo == 0:
                    expectedSequence[idx] = 0x6DB6DB6D
                elif indexNo == 1:
                    expectedSequence[idx] = 0xDB6DB6DB
                else:
                    expectedSequence[idx] = 0xB6DB6DB6
    
            # Bit shift expected sequence by 6 bits
            expectedSequence = self.bitshiftSlowControlArray(expectedSequence, 6)
            
            # Toggle display debug information
            if False:
                self.furtherInformation('testMuxDecoderDefault()', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testMuxDecoderDefault() failed !')
            
        def testDaqBiasDefault(self):
            '''
                Test that the key daq_bias_default works
            '''
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testsDaqBiasDefault_1">
                                    <daq_bias_default value="1"/>
                                </lpd_setup_params>
            '''
        
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            encodedSequence = paramsObj.encode()
    
            # How the sequence should end up looking
            expectedSequence = [0] * LpdAsicSetupParams.SEQLENGTH
    
            expectedSequence[112] = 0x42108420
            expectedSequence[113] = 0x10842108
            expectedSequence[114] = 0x84210842
            expectedSequence[115] = 0x21084210
            expectedSequence[116] = 0x08421084
            expectedSequence[117] = 0x42108421
            expectedSequence[118] = 0x10842108
            expectedSequence[119] = 0x842

            # Bit shift expected sequence by 6 bits
            expectedSequence = self.bitshiftSlowControlArray(expectedSequence, 6)

            # Toggle display debug information
            if False:
                self.furtherInformation('testDaqBiasDefault() (value = 1)', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testDaqBiasDefault() (value = 1) failed !')


            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testsDaqBiasDefault_2">
                                    <daq_bias_default value="31"/>
                                </lpd_setup_params>
            '''

            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            encodedSequence = paramsObj.encode()

            # How the sequence should end up looking
            expectedSequence = [0] * LpdAsicSetupParams.SEQLENGTH

            expectedSequence[112] = 0xFFFFFFFE
            expectedSequence[113] = 0xFFFFFFFF
            expectedSequence[114] = 0xFFFFFFFF
            expectedSequence[115] = 0xFFFFFFFF
            expectedSequence[116] = 0xFFFFFFFF
            expectedSequence[117] = 0xFFFFFFFF
            expectedSequence[118] = 0xFFFFFFFF
            expectedSequence[119] = 0xFFF

            # Bit shift expected sequence by 6 bits
            expectedSequence = self.bitshiftSlowControlArray(expectedSequence, 6)

            # Toggle display debug information
            if False:
                self.furtherInformation('testDaqBiasDefault() (value = 31)', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testDaqBiasDefault() (value = 31) failed !')
    
        def testSelfTestEnable(self):
            '''
                Test that the key self_test_enable works
            '''
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testSelfTestEnable">
                                    <self_test_enable value="1"/>
                                </lpd_setup_params>
            '''
    
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            encodedSequence = paramsObj.encode()

            # How the sequence should end up looking
            expectedSequence = [0] * LpdAsicSetupParams.SEQLENGTH
            expectedSequence[112] = 0x1
    
            # Bit shift expected sequence by 6 bits
            expectedSequence = self.bitshiftSlowControlArray(expectedSequence, 6)
    
            # Toggle display debug information
            if False:
                self.furtherInformation('testSelfTestEnable()', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testSelfTestEnable() failed !')
        
        def testSpareBits(self):
            '''
                Test that the key spare_bits works
            '''
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testSpareBits">
                                    <spare_bits value="31"/>
                                </lpd_setup_params>
            '''

            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            encodedSequence = paramsObj.encode()
    
            # How the sequence should end up looking
            expectedSequence = [0] * LpdAsicSetupParams.SEQLENGTH
    
            # 3820 / 32 = 119; 3820 % 32 = 12
            expectedSequence[119] = 31 << 12
    
            # Bit shift expected sequence by 6 bits
            expectedSequence = self.bitshiftSlowControlArray(expectedSequence, 6)
            
            # Toggle display debug information
            if False:
                self.furtherInformation('testSpareBits()', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testSpareBits() failed !')


        def testFilterControl(self):
            '''
                Test that the key filter_control works
            '''
            filterValue = 1048575
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testFilterControl">
                                    <filter_control value="%i"/>
                                </lpd_setup_params>
            ''' % filterValue
        
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            encodedSequence = paramsObj.encode()
    
            thisIndex = paramsObj.generateBitMask(15)
            
            overflow = ( filterValue >> (32 - 17))
    
            # How the sequence should end up looking
            expectedSequence = [0] * LpdAsicSetupParams.SEQLENGTH
    
            # 3825 / 32 = 119; 3825 % 32 = 17
            expectedSequence[119] = ( (filterValue & thisIndex) << 17)
            expectedSequence[120] = overflow
    
            # Bit shift expected sequence by 6 bits
            expectedSequence = self.bitshiftSlowControlArray(expectedSequence, 6)
    
            # Toggle display debug information
            if False:
                self.furtherInformation('testFilterControl()', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testFilterControl() failed !')


        def testSpecificMuxDecoderValues(self):
            '''
                Test a set of specific mux_decoder key values
            '''
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testSpecificMuxDecoderValues">
                                    <mux_decoder pixel="511" value="3"/>
                                    <mux_decoder pixel="495" value="1"/>
                                    <mux_decoder pixel="479" value="2"/>
                                    <mux_decoder pixel="463" value="5"/>
                                    <mux_decoder pixel="447" value="4"/>
                                    <mux_decoder pixel="431" value="7"/>
                                    <mux_decoder pixel="415" value="6"/>
                                    <mux_decoder pixel="319" value="6"/>
                                    <mux_decoder pixel="159" value="4"/>
                                    <mux_decoder pixel="0" value="2"/>
                                    <mux_decoder pixel="32" value="4"/>
                                    <mux_decoder pixel="64" value="1"/>
                                    <mux_decoder pixel="96" value="1"/>
                                </lpd_setup_params>
            '''
        
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            encodedSequence = paramsObj.encode()
    
            # How the sequence should end up looking
            expectedSequence = [0] * LpdAsicSetupParams.SEQLENGTH
    
            for idx in range(48):
                expectedSequence[idx] = 0x0
            expectedSequence[0] =  0x3E6A980
            expectedSequence[1] =  0xC00
            expectedSequence[2] =  0x100
            expectedSequence[47] = 0x22080000
            expectedSequence[48] = 0x10

            # Toggle display debug information
            if False:
                self.furtherInformation('testSpecificMuxDecoderValues()', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testSpecificMuxDecoderValues() failed !')
    
        def testNewCfgIncludingPreambleDelay(self):
            '''
                Test that using an XML file including preamble delay works
            '''
            thisFile = '/tests/SetupParamsUnitTest.xml'
            currentDir = os.getcwd()
            if currentDir.endswith("LpdFemClient"):
                thisFile = currentDir + thisFile
            else:
                thisFile = currentDir + "/LpdFemClient" + thisFile
        
            theParams = LpdAsicSetupParams(thisFile, preambleBit=6, fromFile=True)
            encodedSequence = theParams.encode()
            
            # How the sequence should end up looking
            expectedSequence = [0x00000000] * LpdAsicSetupParams.SEQLENGTH
            expectedSequence[LpdAsicSetupParams.SEQLENGTH-1] =  0
    
            expectedSequence[112] = 0x4B7B9EB0
            expectedSequence[113] = 0xBB3687A6
            expectedSequence[114] = 0x3EF5354F
            expectedSequence[115] = 0x07A3CA53
            expectedSequence[116] = 0xDD6B419B
            expectedSequence[117] = 0xF64ADED4
            expectedSequence[118] = 0xFBDC8DA3
            expectedSequence[119] = 0x0003B9EC
            expectedSequence[120] = 0x00000400
            expectedSequence[121] = 0x40E1C240
    
            # Toggle display debug information
            if False:
                self.furtherInformation('testNewCfgIncludingPreambleDelay()', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testNewCfgIncludingPreambleDelay() failed !')
    
        def testExternalOverrideValues(self):
            '''
                Test  that the external overrides functionality is working
            '''
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testExternalOverrideValues">
                                    <mux_decoder pixel="511" value="3"/>
                                    <feedback_select_default value="1"/>
                                    <self_test_decoder_default value="2"/>
                                    <mux_decoder pixel="495" value="1"/>
                                    <mux_decoder pixel="479" value="2"/>
                                    <mux_decoder pixel="463" value="5"/>
                                    <mux_decoder pixel="447" value="4"/>
                                    <mux_decoder pixel="431" value="7"/>
                                    <mux_decoder pixel="415" value="6"/>
                                    <mux_decoder pixel="319" value="6"/>
                                    <mux_decoder pixel="159" value="4"/>
                                    <mux_decoder pixel="0" value="2"/>
                                    <mux_decoder pixel="32" value="4"/>
                                    <mux_decoder pixel="64" value="1"/>
                                    <mux_decoder pixel="96" value="1"/>
                                </lpd_setup_params>
            '''
    
            # Parse XML, apply external override values and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, pixelFeedbackOverride=1, pixelSelfTestOverride=4, 
                                           #bDebug=True
                                           preambleBit=6, loadMode=LpdAsicSetupParamsTest.SERIAL) 
            encodedSequence = paramsObj.encode()
            
            # How the sequence should end up looking
            expectedSequence = [0] * LpdAsicSetupParams.SEQLENGTH
    
            for idx in range(48):
                expectedSequence[idx] = 0x0
            expectedSequence[0] =  0x3E6A980
            expectedSequence[1] =  0xC00
            expectedSequence[2] =  0x100
            expectedSequence[47] = 0x22080000
            expectedSequence[48] = 0xCCCCCCD0
            for idx in range(49, 112):
                expectedSequence[idx] = 0xCCCCCCCC
            expectedSequence[112] = 0xC
            
            # Toggle display debug information
            if False:
                self.furtherInformation('testExternalOverrideValues()', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testExternalOverrideValues() failed !')

    
        def testAllKeysAllValues(self):
            '''
                Test all the keys
            '''
            daq_biasValue = 31
            filterValue = 0xFFFFF
            adcValue = filterValue
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testAllKeysAllValues">
                                    <mux_decoder_default value="7"/>
                                    <feedback_select_default value="1"/>
                                    <self_test_decoder_default value="7"/>
                                    <self_test_enable value="1"/>
                                    <daq_bias_default value="%i"/>
                                    <spare_bits value="31"/>
                                    <filter_control value="%i"/>
                                    <adc_clock_delay value="%i"/>
                                    <digital_reserved value="15"/>
                                    <digital_reset3 value="127"/>
                                    <digital_reset2 value="127"/>
                                    <digital_reset1 value="127"/>
                                    <digital_clock_counter_offset value="127"/>
                                </lpd_setup_params>
            ''' % (daq_biasValue, filterValue, adcValue)
            
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, 
                                                       #bDebug=True
                                                       loadMode=0)
            encodedSequence = paramsObj.encode()
                
            
            # How the sequence should end up looking
            expectedSequence = [0xFFFFFFFF] * LpdAsicSetupParams.SEQLENGTH
            expectedSequence[0]= 0xFFFFFFC0
            expectedSequence[ LpdAsicSetupParams.SEQLENGTH-1] = 0
            expectedSequence[ LpdAsicSetupParams.SEQLENGTH-2] = 0x7fffffff
            
            # Toggle display debug information
            if False:
                self.furtherInformation('testAllKeysAllValues()', encodedSequence[0], expectedSequence)
            else:
                self.assertEqual(encodedSequence[0], expectedSequence, 'testAllKeysAllValues() failed !')

        def testNewSyntax(self):
            '''
                Test the new serial loading mode syntax works
            '''
    
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testNewSyntax">
                                    <mux_decoder tile="1" asic="1" pixel="495" value="1"/>
                                    <mux_decoder tile="1" asic="0" pixel="495" value="2"/>
                                    <mux_decoder tile="0" asic="7" pixel="479" value="3"/>
                                    <mux_decoder  asic="0" pixel="511" value="7"/>
                                    <mux_decoder asic="1" pixel="501" value="6"/>
                                    <mux_decoder  asic="2"  value="3"/>
                                </lpd_setup_params>
            '''
    
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, 
                                           #pixelFeedbackOverride=1, pixelSelfTestOverride=2, 
                                           preambleBit=6, loadMode=LpdAsicSetupParamsTest.SERIAL,
                                           #bDebug=True#, debugKey="mux_decoder"
                                           )
            encodedSequence = paramsObj.encode()
    
            # How the sequence should end up looking
            expectedSequence = [[0 for sequence in xrange(LpdAsicSetupParams.SEQLENGTH)] for totalAsics in xrange( 16*8)]
    
            asic = 0
            for idx in range(len(expectedSequence)):
                asic = (idx % 8)
                    
                if (asic % 8 == 0):
                    expectedSequence[idx][0] = expectedSequence[idx][0] + 0x1C0 # <mux_decoder  asic="0" pixel="511" value="7"/>
                if (asic % 8 == 1):
                    expectedSequence[idx][30] = expectedSequence[idx][30] + 0xC0 # <mux_decoder tile="0" asic="0" pixel="501" value="6"/>
                
                if (asic % 8 == 2):
                    for element in range( 48):#                                <mux_decoder  asic="2"  value="3"/>
                        if (element == 0):
                            expectedSequence[idx][element] = expectedSequence[idx][element] + 0xB6DB6D80
                        elif (element % 3 == 1):
                            expectedSequence[idx][element] = expectedSequence[idx][element] + 0x6DB6DB6D  
                        elif (element % 3 == 2):
                            expectedSequence[idx][element] = expectedSequence[idx][element] + 0xDB6DB6DB
                        elif (element % 3 == 0):
                            expectedSequence[idx][element] = expectedSequence[idx][element] + 0xB6DB6DB6 
                    expectedSequence[idx][48] = expectedSequence[idx][48] + 0x36
                    
            expectedSequence[8+1][0] =  0x800       # <mux_decoder tile="1" asic="1" pixel="495" value="1"/>
            expectedSequence[7][0] =  0x6000        # <mux_decoder tile="0" asic="7" pixel="479" value="3"/>
            expectedSequence[8][0] = 0x5C0          # <mux_decoder tile="1" asic="0" pixel="495" value="2"/>
            
            # Toggle display debug information
            if False: #True:#
                self.furtherInformation('testNewSyntax()', encodedSequence, expectedSequence)
            else:
                self.assertEqual(encodedSequence, expectedSequence, 'testNewSyntax() failed !')
    
    
        def testNewSyntaxPartTwo(self):
            '''
                Test the new serial loading mode syntax works
            '''
    
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testNewSyntaxPartTwo">
                                   <mux_decoder value="1"/>
                                </lpd_setup_params>
            '''
    
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, 
                                           #pixelFeedbackOverride=1, pixelSelfTestOverride=2, 
                                           preambleBit=6, loadMode=LpdAsicSetupParamsTest.SERIAL,
    #                                       bDebug=True#, debugKey="mux_decoder"
                                           )
            encodedSequence = paramsObj.encode()
    
            # How the sequence should end up looking
            expectedSequence = [[0 for sequence in xrange(LpdAsicSetupParams.SEQLENGTH)] for totalAsics in xrange( 16*8)]
    
            (tile, asic) = (0, 0)
            for idx in range(len(expectedSequence)):
                asic = (idx % 8)
                if (idx % 8 == 0) and (idx != 0):
                    tile += 1
    
                for element in range( 48):#                                <mux_decoder value="1"/>
                    if (element == 0):
                        expectedSequence[idx][element] = expectedSequence[idx][element] + 0x24924900
                    elif (element % 3 == 1):
                        expectedSequence[idx][element] = expectedSequence[idx][element] + 0x49249249  
                    elif (element % 3 == 2):
                        expectedSequence[idx][element] = expectedSequence[idx][element] + 0x92492492
                    elif (element % 3 == 0):
                        expectedSequence[idx][element] = expectedSequence[idx][element] + 0x24924924 
                expectedSequence[idx][48] = expectedSequence[idx][48] + 0x24
            
            # Toggle display debug information
            if False: #True:#
                self.furtherInformation('testNewSyntaxPartTwo()', encodedSequence, expectedSequence)
            else:
                self.assertEqual(encodedSequence, expectedSequence, 'testNewSyntaxPartTwo() failed !')
 
        def testNewSyntaxPartThree(self):
            '''
                Test the new serial loading mode syntax works
            '''
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="testNewSyntaxPartThree">
                                   <mux_decoder pixel="491" value="4"/>
                                </lpd_setup_params>
            '''
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, 
                                           #pixelFeedbackOverride=1, pixelSelfTestOverride=2, 
                                           #bDebug=True#, debugKey="mux_decoder",
                                           preambleBit=6, loadMode=LpdAsicSetupParamsTest.SERIAL)
            encodedSequence = paramsObj.encode()
     
            # How the sequence should end up looking
            expectedSequence = [[0 for sequence in xrange(LpdAsicSetupParams.SEQLENGTH)] for totalAsics in xrange( 16*8)]
     
            for idx in range(len(expectedSequence)):
                expectedSequence[idx][12] = expectedSequence[idx][12] + 0x200 # <mux_decoder pixel="491" value="4"/>
             
            # Toggle display debug information
            if True:#False: #
                self.furtherInformation('testNewSyntaxPartThree()', encodedSequence, expectedSequence)
            else:
                self.assertEqual(encodedSequence, expectedSequence, 'testNewSyntaxPartThree() failed !')
     
        
        def testDigitalReserved(self):
            '''
                Tests that updating a parameter works as expected
            '''
            digitalReserved = 8
            dictKey = "digital_reserved"    
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="TestString">
                                    <%s value="%i"/>
                                </lpd_setup_params>
            ''' % (dictKey, digitalReserved)
    
            bDebug = False
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6,
                                           #bDebug=True, debugKey="digital_reserved",
                                           loadMode=LpdAsicSetupParamsTest.PARALLEL)
            paramsObj.encode()
            
            # Display an excerp of each dictionary key's value:
            paramsObj.displayDictionaryValues()
      
            # Expected encoded values
            expectedVals = paramsObj.fetchParamsDictionary()[dictKey]
            # The actual values
            digitalReservedVals = paramsObj.getParamValue(dictKey)

            if bDebug: print("digital_reserved:\n", digitalReservedVals[2][0], "expectedVals:\n", expectedVals[2][0])
            self.assertEqual(digitalReservedVals[2][0], expectedVals[2][0], 'testDigitalReserved() failed to update key \"%s\" as expected' % dictKey)
            
            expectedVals = [4, 3865, [digitalReserved]*8, 0, [False, False, False]]
            digitalControlVals = paramsObj.getParamValue(dictKey)
            
            if bDebug: print("Encoded: \n", digitalControlVals, "\n", expectedVals)
            # Compare width, posn, values, skip, tags each agree
            self.assertEqual(digitalControlVals[0],     expectedVals[0], "testDigitalReserved() key \"%s\", 'width' disagree" % dictKey)
            self.assertEqual(digitalControlVals[1],     expectedVals[1], "testDigitalReserved() key \"%s\", 'posn' disagree" % dictKey)
            self.assertEqual(digitalControlVals[2][0],  expectedVals[2], "testDigitalReserved() key \"%s\", 'value' disagree" % dictKey)
            self.assertEqual(digitalControlVals[3],     expectedVals[3], "testDigitalReserved() key \"%s\", 'skip' disagree" % dictKey)
            self.assertEqual(digitalControlVals[4],     expectedVals[4], "testDigitalReserved() key \"%s\", 'tags' disagree" % dictKey)

        def testDigitalReservedExcessiveValue(self):
            '''
                Tests updating digital_reserved beyond valid range throws exception
            '''
            digitalReserved = 16
    
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="TestString">
                                    <digital_reserved value="%i"/>
                                </lpd_setup_params>
            ''' % digitalReserved
    
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            self.assertRaises(LpdAsicSetupParamsInvalidRangeError, paramsObj.encode)
        
        def testDigitalReset3(self):
            '''
                Tests that updating a parameter works as expected
            '''
            digitalReset3 = 8
            dictKey = "digital_reset3"
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="TestDigitalReset3">
                                    <%s value="%i"/>
                                </lpd_setup_params>
            ''' % (dictKey, digitalReset3)
            
            bDebug = False
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6,
                                           #bDebug=True, debugKey="digital_reset3",
                                           loadMode=LpdAsicSetupParamsTest.PARALLEL)
            paramsObj.encode()
            
            # Display an excerp of each dictionary key's value:
            paramsObj.displayDictionaryValues()
            
            # Expected encoded values
            expectedVals = paramsObj.fetchParamsDictionary()[dictKey]
            # The actual values
            digitalReset3Vals = paramsObj.getParamValue(dictKey)
            
            if bDebug: print("digital_reset3:\n", digitalReset3Vals[2][0], "expectedVals:\n", expectedVals[2][0])
            self.assertEqual(digitalReset3Vals[2][0], expectedVals[2][0], 'testDigitalReset3() failed to update key \"%s\" as expected' % dictKey)

            expectedVals = [7, 3869, [digitalReset3]*8, 0, [False, False, False]]
            digitalControlVals = paramsObj.getParamValue(dictKey)
            
            if bDebug: print("Encoded: \n", digitalControlVals, "\n", expectedVals)
            # Compare width, posn, values, skip, tags each agree
            self.assertEqual(digitalControlVals[0],     expectedVals[0], "testDigitalReset3() key \"%s\", 'width' disagree" % dictKey)
            self.assertEqual(digitalControlVals[1],     expectedVals[1], "testDigitalReset3() key \"%s\", 'posn' disagree" % dictKey)
            self.assertEqual(digitalControlVals[2][0],  expectedVals[2], "testDigitalReset3() key \"%s\", 'value' disagree" % dictKey)
            self.assertEqual(digitalControlVals[3],     expectedVals[3], "testDigitalReset3() key \"%s\", 'skip' disagree" % dictKey)
            self.assertEqual(digitalControlVals[4],     expectedVals[4], "testDigitalReset3() key \"%s\", 'tags' disagree" % dictKey)
 
        def testDigitalReset3ExcessiveValue(self):
            '''
                Tests updating digital_reset3 beyond valid range throws exception
            '''
            digitalReset3 = 128
    
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="TestDigitalReset3">
                                    <digital_reset3 value="%i"/>
                                </lpd_setup_params>
            ''' % digitalReset3
    
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            self.assertRaises(LpdAsicSetupParamsInvalidRangeError, paramsObj.encode)
        
        def testDigitalReset2(self):
            '''
                Tests that updating a parameter works as expected
            '''
            digitalReset3 = 8
            dictKey = "digital_reset2"
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="TestDigitalReset2">
                                    <%s value="%i"/>
                                </lpd_setup_params>
            ''' % (dictKey, digitalReset3)
    
            bDebug = False
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, 
                                           #bDebug=True, debugKey="digital_reset2",
                                           loadMode=LpdAsicSetupParamsTest.PARALLEL)
            paramsObj.encode()
            
            # Display an excerp of each dictionary key's value:
            paramsObj.displayDictionaryValues()
            
            # Expected encoded values
            expectedVals = paramsObj.fetchParamsDictionary()[dictKey]
            # The actual values
            digitalReset2Vals = paramsObj.getParamValue(dictKey)

            if bDebug: print("digital_reset2:\n", digitalReset2Vals[2][0], "expectedVals:\n", expectedVals[2][0])
            self.assertEqual(digitalReset2Vals[2][0], expectedVals[2][0], 'testDigitalReset2() failed to update key \"%s\" as expected' % dictKey)

            expectedVals = [7, 3876, [digitalReset3]*8, 0, [False, False, False]]
            digitalControlVals = paramsObj.getParamValue(dictKey)
            
            if bDebug: print("Encoded: \n", digitalControlVals, "\n", expectedVals)
            # Compare width, posn, values, skip, tags each agree
            self.assertEqual(digitalControlVals[0],     expectedVals[0], "testDigitalReset2() key \"%s\", 'width' disagree" % dictKey)
            self.assertEqual(digitalControlVals[1],     expectedVals[1], "testDigitalReset2() key \"%s\", 'posn' disagree" % dictKey)
            self.assertEqual(digitalControlVals[2][0],  expectedVals[2], "testDigitalReset2() key \"%s\", 'value' disagree" % dictKey)
            self.assertEqual(digitalControlVals[3],     expectedVals[3], "testDigitalReset2() key \"%s\", 'skip' disagree" % dictKey)
            self.assertEqual(digitalControlVals[4],     expectedVals[4], "testDigitalReset2() key \"%s\", 'tags' disagree" % dictKey)
 
        def testDigitalReset2ExcessiveValue(self):
            '''
                Tests updating digital_reset2 beyond valid range throws exception
            '''
            digitalReset3 = 128
    
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="TestDigitalReset2">
                                    <digital_reset2 value="%i"/>
                                </lpd_setup_params>
            ''' % digitalReset3
    
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            self.assertRaises(LpdAsicSetupParamsInvalidRangeError, paramsObj.encode)
    
    
        def testDigitalReset1(self):
            '''
                Tests that updating a parameter works as expected
            '''
            digitalReset1 = 8
            dictKey = "digital_reset1"
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="TestDigitalReset1">
                                    <%s value="%i"/>
                                </lpd_setup_params>
            ''' % (dictKey, digitalReset1)
    
            bDebug = False #True
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, 
                                           #bDebug=True, debugKey="digital_reset2",
                                           loadMode=LpdAsicSetupParamsTest.PARALLEL)
            paramsObj.encode()
            
            # Display an excerp of each dictionary key's value:
            paramsObj.displayDictionaryValues()
            
            # Expected encoded values
            expectedVals = paramsObj.fetchParamsDictionary()[dictKey]
            # The actual values
            digitalReset1Vals = paramsObj.getParamValue(dictKey)

            if bDebug: print("digital_reset2:\n", digitalReset1Vals[2][0], "expectedVals:\n", expectedVals[2][0])
            self.assertEqual(digitalReset1Vals[2][0], expectedVals[2][0], 'testDigitalReset1() failed to update key \"%s\" as expected' % dictKey)
    
            expectedVals = [7, 3883, [digitalReset1]*8, 0, [False, False, False]]
    
            digitalControlVals = paramsObj.getParamValue(dictKey)
            
            if bDebug: print("Encoded: \n", digitalControlVals, "\n", expectedVals)
            # Compare width, posn, values, skip, tags each agree
            self.assertEqual(digitalControlVals[0],     expectedVals[0], "testDigitalReset1() key \"%s\", 'width' disagree" % dictKey)
            self.assertEqual(digitalControlVals[1],     expectedVals[1], "testDigitalReset1() key \"%s\", 'posn' disagree" % dictKey)
            self.assertEqual(digitalControlVals[2][0],  expectedVals[2], "testDigitalReset1() key \"%s\", 'value' disagree" % dictKey)
            self.assertEqual(digitalControlVals[3],     expectedVals[3], "testDigitalReset1() key \"%s\", 'skip' disagree" % dictKey)
            self.assertEqual(digitalControlVals[4],     expectedVals[4], "testDigitalReset1() key \"%s\", 'tags' disagree" % dictKey)
 
        def testDigitalReset1ExcessiveValue(self):
            '''
                Tests updating digital_reset2 beyond valid range throws exception
            '''
            digitalReset3 = 128
    
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="TestDigitalReset1">
                                    <digital_reset2 value="%i"/>
                                </lpd_setup_params>
            ''' % digitalReset3
    
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            self.assertRaises(LpdAsicSetupParamsInvalidRangeError, paramsObj.encode)
    
        def testDigitalClockCounterOffset(self):
            '''
                Tests that updating a parameter works as expected
            '''
            digitalClockCounterOffset = 8
            dictKey = "digital_clock_counter_offset"
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="TestDigitalClockCounterOffset">
                                    <%s value="%i"/>
                                </lpd_setup_params>
            ''' % (dictKey, digitalClockCounterOffset)
    
            bDebug = False
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, 
                                           #bDebug=True, debugKey="digital_clock_counter_offset",
                                           loadMode=LpdAsicSetupParamsTest.PARALLEL)
            paramsObj.encode()
            
            # Display an excerp of each dictionary key's value:
            paramsObj.displayDictionaryValues()
      
            # Expected encoded values
            expectedVals = paramsObj.fetchParamsDictionary()[dictKey]
            # The actual values
            digitalCCOVals = paramsObj.getParamValue(dictKey)

            if bDebug: print("digital_clock_counter_offset:\n", digitalCCOVals[2][0], "expectedVals:\n", expectedVals[2][0])
            self.assertEqual(digitalCCOVals[2][0], expectedVals[2][0], 'testDigitalClockCounterOffset() failed to update key \"%s\" as expected' % dictKey)

            expectedVals = [7, 3890, [digitalClockCounterOffset]*8, 0, [False, False, False]]
            digitalControlVals = paramsObj.getParamValue(dictKey)
            
            if bDebug: print("Encoded: \n", digitalControlVals, "\n", expectedVals)
            # Compare width, posn, values, skip, tags each agree
            self.assertEqual(digitalControlVals[0],     expectedVals[0], "testDigitalClockCounterOffset() key \"%s\", 'width' disagree" % dictKey)
            self.assertEqual(digitalControlVals[1],     expectedVals[1], "testDigitalClockCounterOffset() key \"%s\", 'posn' disagree" % dictKey)
            self.assertEqual(digitalControlVals[2][0],  expectedVals[2], "testDigitalClockCounterOffset() key \"%s\", 'value' disagree" % dictKey)
            self.assertEqual(digitalControlVals[3],     expectedVals[3], "testDigitalClockCounterOffset() key \"%s\", 'skip' disagree" % dictKey)
            self.assertEqual(digitalControlVals[4],     expectedVals[4], "testDigitalClockCounterOffset() key \"%s\", 'tags' disagree" % dictKey)
 
        def testDigitalClockCounterOffsetExcessiveValue(self):
            '''
                Tests updating digital_clock_counter_offset beyond valid range throws exception
            '''
            digitalClockCounterOffset = 128
    
            stringCmdXml = '''<?xml version="1.0"?>
                                <lpd_setup_params name="TestDigitalClockCounterOffset">
                                    <digital_clock_counter_offset value="%i"/>
                                </lpd_setup_params>
            ''' % digitalClockCounterOffset
    
            # Parse XML and encode
            paramsObj = LpdAsicSetupParams(stringCmdXml, preambleBit=6, loadMode=LpdAsicSetupParamsTest.PARALLEL)
            self.assertRaises(LpdAsicSetupParamsInvalidRangeError, paramsObj.encode)
    
    def furtherInformation (self, parent, encoded, expected):
        '''
            Provide further debug information when a unit test fails
        '''
        (tile, asic) = (0, 0)
        for index in range( len(encoded)):
            asic = (index % 8)
            if (index  % 8 == 0) and (index != 0):
                tile += 1
            try:
                self.assertEqual(encoded[index], expected[index], '')
            except:
                try:
                    for element in range( len( encoded[0])):
                        self.assertEqual(encoded[index][element], expected[index][element], '')
                except:
                    print("\nError: Tile[%2i] ASIC[%1i] Element[%i]" % (tile, asic, element), " Encoded: 0x%X Expected: 0x%X" % ( encoded[index][element], expected[index][element]))
                    print("\n encodedSequence: ")
                    self.displaySequence(encoded[index])
                    print(" expectedSequence: ")
                    self.displaySequence(expected[index])
                    self.assertEqual(encoded[index][element], expected[index][element], parent+" failed!")
                    
        
    def displaySequence(self, seq):
        '''
            Helper function for unit testing, displays the contents of argument 'seq' sequence 
        '''
        for idx in range(len(seq)):
            if idx > 271:
                continue
            if (idx % 16 == 0):
                print("\n%3i: " % idx, end="")
            print("%9X" % seq[idx], end="")
        print("\n")

    def bitshiftSlowControlArray(self, seq, numBits):
        '''
            Helper function: (Left-)bitshift sequence 'seq' by 'numBits' bits  
        '''
        lastIndexExcess = 0
        for idx in range(len(seq)):
            # Bitshift
            seq[idx] = seq[idx] << numBits
            # Add any bits shifted in from the previous index
            seq[idx] = seq[idx] | lastIndexExcess
            # Save anything beyond the 32 bit boundary for the next index
            lastIndexExcess = seq[idx] >> 32
            # Throwaway any bits beyond the 32 bit boundary
            seq[idx]= seq[idx] & 0xFFFFFFFF
        
        return seq

if __name__ == '__main__':
    
    # Execute unit testing
    unittest.main()
    
