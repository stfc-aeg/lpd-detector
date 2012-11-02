# Check in setParaValue() for list/integer type 
import types, sys

from xml.etree.ElementInclude import ElementTree
from xml.etree.ElementTree import ParseError

# Define Exception Class
class SlowCtrlParamsInvalidRangeError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)

class SlowCtrlParamsError(Exception):
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)


class SlowCtrlParams(object):
 
    # Class Constants
    SEQLENGTH = 123

    # xml lookup tables
    '''
                !
        NOTE: these are based upon a slow control numbering of pixels 1-512, index 1-47
                but whenever they are used they are subtracted by one to match 
                Python numbering of pixel 0-512, index 0-46
                
                !
    '''
    biasCtrlLookupTable = [ 47, 46, 21, 15,  9, 36, 45, 19, 14,  8, 44, 
                            32, 18, 12,  5, 43, 30, 17, 11,  2, 42, 24, 
                            16, 10,  1, 41, 37, 28, 23,  7, 35, 33, 27, 
                            22,  6, 40, 31, 26, 20,  4, 39, 29, 25, 13, 
                             3, 38, 34]
    
    muxDecoderLookupTable = [512, 496, 480, 464, 448, 432, 416, 400, 
                             384, 368, 352, 336, 320, 304, 288, 272, 
                             256, 240, 224, 208, 192, 176, 160, 144, 
                             128, 112,  96,  80,  64,  48,  32,  16, 
                             511, 495, 479, 463, 447, 431, 415, 399, 
                             383, 367, 351, 335, 319, 303, 287, 271, 
                             255, 239, 223, 207, 191, 175, 159, 143, 
                             127, 111,  95,  79,  63,  47,  31,  15, 
                             510, 494, 478, 462, 446, 430, 414, 398, 
                             382, 366, 350, 334, 318, 302, 286, 270, 
                             254, 238, 222, 206, 190, 174, 158, 142, 
                             126, 110,  94,  78,  62,  46,  30,  14, 
                             509, 493, 477, 461, 445, 429, 413, 397, 
                             381, 365, 349, 333, 317, 301, 285, 269, 
                             253, 237, 221, 205, 189, 173, 157, 141, 
                             125, 109,  93,  77,  61,  45,  29,  13, 
                             508, 492, 476, 460, 444, 428, 412, 396, 
                             380, 364, 348, 332, 316, 300, 284, 268, 
                             252, 236, 220, 204, 188, 172, 156, 140, 
                             124, 108,  92,  76,  60,  44,  28,  12, 
                             507, 491, 475, 459, 443, 427, 411, 395, 
                             379, 363, 347, 331, 315, 299, 283, 267, 
                             251, 235, 219, 203, 187, 171, 155, 139, 
                             123, 107,  91,  75,  59,  43,  27,  11, 
                             506, 490, 474, 458, 442, 426, 410, 394, 
                             378, 362, 346, 330, 314, 298, 282, 266, 
                             250, 234, 218, 202, 186, 170, 154, 138, 
                             122, 106,  90,  74,  58,  42,  26,  10, 
                             505, 489, 473, 457, 441, 425, 409, 393, 
                             377, 361, 345, 329, 313, 297, 281, 265, 
                             249, 233, 217, 201, 185, 169, 153, 137, 
                             121, 105,  89,  73,  57,  41,  25,   9,
                             504, 488, 472, 456, 440, 424, 408, 392, 
                             376, 360, 344, 328, 312, 296, 280, 264, 
                             248, 232, 216, 200, 184, 168, 152, 136, 
                             120, 104,  88,  72,  56,  40,  24,   8, 
                             503, 487, 471, 455, 439, 423, 407, 391, 
                             375, 359, 343, 327, 311, 295, 279, 263, 
                             247, 231, 215, 199, 183, 167, 151, 135, 
                             119, 103,  87,  71,  55,  39,  23,   7, 
                             502, 486, 470, 454, 438, 422, 406, 390, 
                             374, 358, 342, 326, 310, 294, 278, 262, 
                             246, 230, 214, 198, 182, 166, 150, 134, 
                             118, 102,  86,  70,  54,  38,  22,   6, 
                             501, 485, 469, 453, 437, 421, 405, 389, 
                             373, 357, 341, 325, 309, 293, 277, 261, 
                             245, 229, 213, 197, 181, 165, 149, 133, 
                             117, 101,  85,  69,  53,  37,  21,   5,
                             500, 484, 468, 452, 436, 420, 404, 388, 
                             372, 356, 340, 324, 308, 292, 276, 260, 
                             244, 228, 212, 196, 180, 164, 148, 132, 
                             116, 100,  84,  68,  52,  36,  20,   4, 
                             499, 483, 467, 451, 435, 419, 403, 387, 
                             371, 355, 339, 323, 307, 291, 275, 259, 
                             243, 227, 211, 195, 179, 163, 147, 131, 
                             115,  99,  83,  67,  51,  35,  19,   3, 
                             498, 482, 466, 450, 434, 418, 402, 386, 
                             370, 354, 338, 322, 306, 290, 274, 258, 
                             242, 226, 210, 194, 178, 162, 146, 130, 
                             114,  98,  82,  66,  50,  34,  18,   2, 
                             497, 481, 465, 449, 433, 417, 401, 385, 
                             369, 353, 337, 321, 305, 289, 273, 257, 
                             241, 225, 209, 193, 177, 161, 145, 129, 
                             113,  97,  81,  65,  49,  33,  17,   1 ]

    pixelSelfTestLookupTable = [497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 
                                496, 495, 494, 493, 492, 491, 490, 489, 488, 487, 486, 485, 484, 483, 482, 481, 
                                465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 
                                464, 463, 462, 461, 460, 459, 458, 457, 456, 455, 454, 453, 452, 451, 450, 449, 
                                433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 
                                432, 431, 430, 429, 428, 427, 426, 425, 424, 423, 422, 421, 420, 419, 418, 417, 
                                401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 
                                400, 399, 398, 397, 396, 395, 394, 393, 392, 391, 390, 389, 388, 387, 386, 385, 
                                369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 
                                368, 367, 366, 365, 364, 363, 362, 361, 360, 359, 358, 357, 356, 355, 354, 353, 
                                337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 
                                336, 335, 334, 333, 332, 331, 330, 329, 328, 327, 326, 325, 324, 323, 322, 321, 
                                305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 
                                304, 303, 302, 301, 300, 299, 298, 297, 296, 295, 294, 293, 292, 291, 290, 289, 
                                273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 
                                272, 271, 270, 269, 268, 267, 266, 265, 264, 263, 262, 261, 260, 259, 258, 257, 
                                241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 
                                240, 239, 238, 237, 236, 235, 234, 233, 232, 231, 230, 229, 228, 227, 226, 225, 
                                209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 
                                208, 207, 206, 205, 204, 203, 202, 201, 200, 199, 198, 197, 196, 195, 194, 193, 
                                177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 
                                176, 175, 174, 173, 172, 171, 170, 169, 168, 167, 166, 165, 164, 163, 162, 161, 
                                145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 
                                144, 143, 142, 141, 140, 139, 138, 137, 136, 135, 134, 133, 132, 131, 130, 129, 
                                113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 
                                112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100,  99,  98,  97, 
                                 81,  82,  83,  84,  85,  86,  87,  88,  89,  90,  91,  92,  93,  94,  95,  96, 
                                 80,  79,  78,  77,  76,  75,  74,  73,  72,  71,  70,  69,  68,  67,  66,  65, 
                                 49,  50,  51,  52,  53,  54,  55,  56,  57,  58,  59,  60,  61,  62,  63,  64, 
                                 48,  47,  46,  45,  44,  43,  42,  41,  40,  39,  38,  37,  36,  35,  34,  33, 
                                 17,  18,  19,  20,  21,  22,  23,  24,  25,  26,  27,  28,  29,  30,  31,  32, 
                                 16,  15,  14,  13,  12,  11,  10,   9,   8,   7,   6,   5,   4,   3,   2,   1, ]


    def __init__(self, xmlObject, fromFile=False, strict=True):
        #TODO: Sort out argument list - will have implications wherever objects are created of this class
        strict = True
        # Set the strict syntax flag to specified value (defaults to true)
        self.strict = strict
        
        ''' Debug info: '''
        self.bDebug = False

        if self.bDebug:
            print "debugging enabled."

        #    paramsDict = {'dictKey'                     : [width, posn, value(s), [bPixelTagRequired, bValueTagRequired, bIndexTagRequired]}
        self.paramsDict = {'mux_decoder_default'         : [3,  -1,     -1,         [False, True, False]],
                           'mux_decoder'                 : [3,  0,      [-1] * 512, [True,  True, False]],
                           'feedback_select_default'     : [1,  -1,     -1,         [False, True, False]],
                           'feedback_select'             : [1,  1536,   [-1] * 512, [True,  True, False]],
                           'self_test_decoder_default'   : [3,  -1,     -1,         [False, True, False]],
                           'self_test_decoder'           : [3,  1537,   [-1] * 512, [True,  True, False]],
                           'self_test_enable'            : [1,  3584,   -1,         [False, True, False]],
                           'daq_bias_default'            : [5,  -1,     -1,         [False, True, False]],
                           'daq_bias'                    : [5,  3585,   [-1] * 47,  [False, True, True]],
                           'spare_bits'                  : [5,  3820,   -1,         [False, True, False]],        # Special Case: 5 bits cover everything
                           'filter_control'              : [20, 3825,   -1,         [False, True, False]],       # Special Case: 20 bits cover everything
                           'adc_clock_delay'             : [20, 3845,   -1,         [False, True, False]],       # Special Case: 20 bits cover everything
                           'digital_control'             : [40, 3865,   -1,         [False, True, False]],       # Special Case: 40 bits cover everything
                           }
        # Definition of position of fast command fields in BRAM words
#        self.sync = 1
#        self.sync_pos = 21
#        self.nop_pos  = 22
#        self.cmd_pos  = 12
#        self.sync_reset_pos = 2

        # Count total number of nops
#        self.total_number_nops = 0
        
        # Count total number of words
#        self.total_number_words = 0
        
        ''' Debug information '''
        if self.bDebug:
            print "Class initialising, reading file or string = "
            print xmlObject
            
        #TODO: Implemented this:
        # Parse the XML specified, either from a file if the fromFile flag
        # was set or from the string passed
        if fromFile == True:
            self.tree = ElementTree.parse(xmlObject)
            self.root = self.tree.getroot()
        else:
            self.tree = None 
            self.root = ElementTree.fromstring(xmlObject)
        
        # Get the root of the tree and verify it is an lpd_command_sequence
        if self.root.tag != 'lpd_slow_ctrl_sequence':
            raise SlowCtrlParamsError('Root element is not an LPD slow control command')

        

    def getParamValue(self, dictKey):
        ''' Obtains the three variables associated with the dictionary key 'dictKey' 
            and returns them as three variables (the third are in some cases a list) '''
        
        width = 0xdeadbeef
        posn = 0xDeadBeef
        val = 0xDeadBeef
        
        # Does dictKey exist in the dictionary?
        if dictKey in self.paramsDict:
            result = self.paramsDict[dictKey]
            
            width = result[0]
            posn = result[1]
            val = result[2]
            tags = result[3]
        else:
            print "\"" + dictKey + "\" doesn't exist."
        
        return [width, posn, val, tags]
 
    def setParamValue(self, dictKey, index, value):
        ''' 
            Updates the dictionary key 'dictKey' with the new value in 'value', 
            overwriting whatever used to be at position 'index'
            
            Note: Python starts any list with 0, therefore first pixel = 0, second pixel = 1, etc.
                (Slow Control documentation states pixel 1 is the first, but disregard that)
        '''
                        
        # Does dictKey exist in the dictionary?
        if dictKey in self.paramsDict:
                        
            # Save the current key's values that we (may) want to retain
            currentValue = self.paramsDict[dictKey]

            # Check that the new value is within valid range
            if not (0 <= value <= ( (2**currentValue[0]) -1) ):
                raise SlowCtrlParamsInvalidRangeError("%s's value outside valid range, max: %i received: %i" % (dictKey, 2**currentValue[0]-1, value) )
            
            else:
                # Is the third variable a list or an integer?
                if isinstance(currentValue[2], types.ListType):
                    # it's a list; Update the new value
                    currentValue[2][index] = value
                    
                elif isinstance(currentValue[2], types.IntType):
                    currentValue[2] = value
                else:
                    print "SetParamValue() Error: currentValue[2] is neither a list nor an integer!"
                                    
                # Overwrite the old value
                self.paramsDict[dictKey] = currentValue

        else:
            print "\"" + dictKey + "\" doesn't exist."
            
    def encode(self):
        '''
        Encodes the  slow control command(s)..
        '''

        # Intialise tree depth (used for debugging only)
        self.depth = 0
        
        # Parse the tree, starting at the root element, obtaining the packed
        #     binary command sequence as a list
        self.parseElement(self.root)
        
        #TODO: sort this out; sequence should come from the buildBitstream() function ??
        sequence  = self.buildBitstream()
        
        # Count the total number of words
#        self.total_number_words = len(sequence)
        
        # Return the command sequence
        return sequence

    def getAttrib(self, theElement, theAttrib):
        '''
        Returns the value of the theAttrib attribute of the specified element if it exists,
        or a default value of 1 if not. Can also throw an exception if a non-integer
        attribute is detected
        '''
        if self.bDebug:
            print "attrib: '" + theAttrib + "'",
        
        # Get the attribute or a default value of -2 (differentiate from unspecified value which is -1)
        intAttrib = theElement.get(theAttrib, default='-2')
        
        if self.bDebug:
            print " is: %3s" % intAttrib + ".",
        # Convert count to integer or raise an exception if this failed
        try:
            attrib = int(intAttrib)
        except ValueError:
            raise SlowCtrlParamsError('Non-integer attribute specified')
        
        # Return integer attrib value    
        return attrib

    def doLookupTableCheck(self, dictKey, idx):
        '''
            Accepts the dictionary key dictKey an and associated index 'idx'
        '''
        # Does dictKey have an associated lookup table?
        if dictKey == "mux_decoder":
            return (SlowCtrlParams.muxDecoderLookupTable[idx] - 1)
        elif dictKey == "feedback_select":
            return (SlowCtrlParams.pixelSelfTestLookupTable[idx] - 1)
        elif dictKey == "self_test_decoder":
            return (SlowCtrlParams.pixelSelfTestLookupTable[idx] - 1)
        elif dictKey == "daq_bias":
            return (SlowCtrlParams.biasCtrlLookupTable[idx] - 1)
        else:
#            raise SlowCtrlParamsError("Invalid execution: No lookup table for key '%s'!" % dictKey)
            return idx             
        
    def parseElement(self, theElement):
        '''
            Parses an element (partial tree) of the XML command sequence, encoding commands
            into the appropriate values and returning them. Note that slow control is more complicated
            because each parameter is inserted into the slow control bitstream according to its relative position.
            
            NOTE: pixels run 1-512, index 1-47 but to match Python's lists they're numbered 0-511, 0-46.
        '''
        
        # Increment tree depth counter
        self.depth = self.depth + 1

        # The structure of the parameters to dictionary is:
        # paramsDict = {'dictKey' : [width, posn, value(s), [bPixelTagRequired, bValueTagRequired, bIndexTagRequired]}
        #     where values(s) is an integer or a list and the nested list of booleans defines which tags that are required

#        print "mux_decoder_default: ", self.paramsDict['mux_decoder_default'], "\n"
#        print "mux_decoder: ", self.paramsDict['mux_decoder']

        # Loop over child nodes of the current element
        for child in theElement:

            # Get the command name (tag) for the current element
            cmd = child.tag
                         
            # Check this command is in the syntax dictionary and process
            # accordingly. Raise an exception if the command is not recognised and
            # strict syntax checking is enabled
            if cmd in self.paramsDict:

                if self.bDebug:
                    print "\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n", cmd,
                
                # get parameter values
                pmValues = self.getParamValue(cmd)

                # Extract required tags
                bPixel = pmValues[3][0]
                bValue = pmValues[3][1]
                bIndex = pmValues[3][2]
                
                # Get value attribute (always present)
                value = self.getAttrib(child, 'value')
                if value == -2:
                    # Fail if there is no value present
                    raise SlowCtrlParamsError("Unable to find the required 'value' tag for key '%s'!" % cmd)
                
                if self.bDebug:
                    print "value = ", value,
                
                # is there a pixel tag?
                if bPixel:
                    # Get pixel
                    pixel = self.getAttrib(child, 'pixel')
                    
                    # Use pixel number to obtain pixel order using the lookup table function (where applicable)
                    orderedPxl = self.doLookupTableCheck(cmd, pixel)
                    
                    if self.bDebug:
                        print " pixel, orderedPxl = %3i, %3i" % (pixel, orderedPxl),
                    # Update pixel entry of the dictionary key
                    self.setParamValue(cmd, orderedPxl, value)
                    ''' DO NOT UPDATED THE ASSOCIATED KEY! '''
#                    # Does the current key have an associated _default key?
#                    if (cmd+"_default") in self.paramsDict:
#                        # Yes it does, update pixel in associated key
#                        self.setParamValue( (cmd+"_default"), orderedPxl, value)
#                        #print "Yes, %s has an associated key: %s." % (cmd, cmd) 
                else:
                    # Is there a index tag?
                    if bIndex:
                        index = self.getAttrib(child, 'index')
                        
                        # Use index to obtain index order using the lookup table function (where applicable)
                        orderedIdx = self.doLookupTableCheck(cmd, index)
                        
                        if self.bDebug:
                            print " index, orderedIdx = %3i, %3i" % (index, orderedIdx)
                        # Update index entry of the dictionary key
                        self.setParamValue(cmd, orderedIdx, value)
                    else:
                        # No pixel, no index tags: therefore the key's value
                        #     is a simple integer to update
                        self.setParamValue(cmd, 0, value)
                
            else:
                if self.strict:
                    raise SlowCtrlParamsError('Illegal command %s specified' % (child.tag))
        
        if self.bDebug:
            print "\n\n~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~"
        
#        print "mux_decoder_default: ", self.paramsDict['mux_decoder_default'], "\n"
#        print "mux_decoder: ", self.paramsDict['mux_decoder']

        # Pass through XXX_default keys and change their value from -1 to 0 unless already set
        for key in self.paramsDict:
            # Is this a XXX_default key?
            if key.endswith("_default"):
                if self.bDebug:
                    print "1st: Found _default key: ", key, " = ",

                # Obtain its value
                defaultKeyValue = self.getParamValue(key)
                if self.bDebug:
                    print defaultKeyValue,

                # Is XXX_default not specified ?
                if defaultKeyValue[2] == -1:
                    # Default not set; set the _default key's value to 0
                    self.setParamValue(key, 0, 0)
                    if self.bDebug:
                        print " now = ", self.getParamValue(key)[2]
                else:
                    if self.bDebug:
                        print " (no change)"
                    
        if self.bDebug:
            print "- - - - - - - - - - - - - - - - - - - - -"
        
        # Check _default keys and updated the corresponding keys unless they have been explicitly set
        #    e.g. if daq_bias_default = 4 them all values of daq_bias will become 4 (unless set explicitly)

        for key in self.paramsDict:
            # Is this a XXX_default key?
            if key.endswith("_default"):

                if self.bDebug:
                    print "2nd: Found _default key: ", key, " = ",

                # Obtain its value
                defaultKeyValue = self.getParamValue(key)
                if self.bDebug:
                    print defaultKeyValue
                
                # Derive corresponding key's name
                #    e.g. key = "mux_decoder_default"; sectionKey = "mux_decoder"
                sectionKey = key.replace("_default", "")
                sectionKeyValue = self.getParamValue(sectionKey)
                sectionKeyLength = len(sectionKeyValue[2])

#                # Is XXX_default not specified ?
#                if defaultKeyValue[2] == -1:
#                    # Default not set; set the _default key's value to 0
#                    self.setParamValue(key, 0, 0)
#                    # Check the section key values and update any index that is still -1
#                    for idx in range(sectionKeyLength):
#                        # Update only if pixel not already explicitly set
#                        if sectionKeyValue[2][idx] == -1:
#                            # -1 denotes pixel hasn't been explicitly set; set it to 0
#                            self.setParamValue(sectionKey, idx, 0)
#                    
#                else:
#                    # Default is set; Update any entry not explicitly set with default value
#                    print "Dead END!"
#                    print "_______________________________________________________________________________________________________________________________________________"
#                    print "Just about to hit the following values: ", sectionKeyValue[2]

                # Updates all values of the key except any that have already been explicitly set
                for idx in range(sectionKeyLength):
                    # Update only if pixel not explicitly set
                    if sectionKeyValue[2][idx] == -1:
                        # -1 denotes pixel hasn't been explicitly set; go ahead and update it
                        self.setParamValue(sectionKey, idx, defaultKeyValue[2])


            else:
                # All keys that does not end with "_default"
                #    Of of these keys, 5 have single integer value, 4 have nested list of values
                #    The 4 that had nested lists of values can be ignored (already covered in the if statement above)
                
                # 
                keyValue = self.getParamValue(key)
#                print "Going to check this type: ", keyValue[2]
                if isinstance(keyValue[2], types.IntType):
                    if self.bDebug:
                        print "%21s: It's an integer type" % key
                    
                    # Has the value been set?
                    if keyValue[2] == -1:
                        # Not set; Set it to 0
                        self.setParamValue(key, 0, 0)


                
                    
        # Back up one level in the tree              
        self.depth = self.depth - 1

        if self.bDebug:
            print "______________________________________________________________________________________"
            print "                FINISHED"
            print "______________________________________________________________________________________"
#        print "mux_decoder_default: ", self.paramsDict['mux_decoder_default'], "\n"
#        print "mux_decoder: ", self.paramsDict['mux_decoder']
        
#        print self.paramsDict['mux_decoder_default']
#        print self.paramsDict['mux_decoder']             
#        print self.paramsDict['feedback_select_default'] 
#        print self.paramsDict['feedback_select']         
#        print self.paramsDict['self_test_decoder_default']
#        print self.paramsDict['self_test_decoder']       
#        print self.paramsDict['self_test_enable']        
#        print self.paramsDict['daq_bias_default']        
#        print self.paramsDict['daq_bias']                
#        print self.paramsDict['spare_bits']              
#        print self.paramsDict['filter_control']          
#        print self.paramsDict['adc_clock_delay']         
#        print self.paramsDict['digital_control']         

 
    def buildBitstream(self):
        '''
            Loop over dictionary keys and building the word bitstream programmatically
        '''

        ''' Debug variables '''
        debugIdx = 33
        debugComparisonKey = ""    # "spare_bits"    # "self_test_decoder"    # "mux_decoder"    # "digital_control"

        # Initialise empty list to contain binary command values for this part of the tree
        encodedSequence = [0] * SlowCtrlParams.SEQLENGTH
        
        # Loop over dictionary entries 
        for dictKey in self.paramsDict:

            # If it is a XX_default key, do not process it
            if dictKey.endswith("_default"):
                continue
            else:

                # Get dictionary values for this key
                cmdParams = self.getParamValue(dictKey)
                # word width of this key?
                keyWidth = cmdParams[0]
                # Where does current key reside within the sequence?
                wordPosition = cmdParams[1] / 32
                # Slow Control Value(s)
                slowControlWordContent = cmdParams[2]
                # bitPosition tracks the current bit position relative to the entire length of sequence
                bitPosition = cmdParams[1]
                
                # Is this a list?
                if isinstance(slowControlWordContent, types.ListType):

                    # Determine number of entries in the nested list
                    numBitsRequired = len(slowControlWordContent)

                    # Key: "self_test_decoder" and "feedback_select" share a 4 bit slow control word
                    #    and therefore form a special case (set to 0 for all other keys)
                    
                    # Is this key either of the two special cases?
                    if dictKey.startswith("feedback_select"):
                        specialCaseOffset = 3
                    elif dictKey.startswith("self_test_decoder"):
                        specialCaseOffset = 1
                    else:
                        specialCaseOffset = 0
                        
                    keyWidth = keyWidth + specialCaseOffset
                    # Create a bit array to save each slow control word bit by bit
                    bitwiseArray = [0] * (keyWidth * numBitsRequired)

                    ''' 
                        LIST TYPE: FIRST LOOP
                    '''
                    # Loop over all the elements of the nested list and produce bitwiseArray
                    #    e.g.: if keyWidth = 3, list = [1, 3, 0, .] then bitwiseOffset = [ (1, 0, 0,) (1, 1, 1,) (0, 0, 0,) ..]
                    for idx in range(numBitsRequired):
                        
                        bitMask = 1
                        # Iterate over each bit of each slow control word
                        for bitIdx in range(keyWidth):
                            bitwiseArray[ idx*keyWidth + bitIdx ] = ( (slowControlWordContent[idx] & bitMask) >> bitIdx)
                            bitMask = bitMask << 1
                                        
                    '''
                        LIST TYPE: SECOND LOOP
                    '''
                    # Loop over this new list and chop each 32 bits into the encoded sequence
                    for idx in range(len(bitwiseArray)):
#                        ''' DEBUG INFO '''
#                        if dictKey == debugComparisonKey:
#                            if idx < 42:
#                                print "idx=%3i, bitPosn=%2i, seqIdxTotal:%9X" % (idx, bitPosition%32, bitwiseArray[idx] << (bitPosition%32)),
#                                print " (%i << %2i) " % (bitwiseArray[idx], (bitPosition%32)),
#                                print "= %9X" % (bitwiseArray[idx] << (bitPosition%32)),
#                                print " encSeq[%3i] = %9X" % (wordPosition, encodedSequence[wordPosition]) 
                        
                        # Add running total to sequence; increment bitPosition and check wordPosition 
                        encodedSequence[wordPosition] = encodedSequence[wordPosition] | (bitwiseArray[idx] << (bitPosition%32))
                        bitPosition += 1
                        wordPosition = bitPosition / 32
                else:
                    '''
                        INTEGER TYPE
                    '''
                    # Need not update encoded sequence if slow control word empty
                    if slowControlWordContent == 0:
                        continue

                    # Split the integer into bitwise array
                    numBitsRequired = cmdParams[0]
                    # Create a bit array to save each bit individually from the slow control word
                    bitwiseArray = [0] * numBitsRequired                    
                    
                    '''
                        INTEGER TYPE: FIRST LOOP
                    '''
                    bitMask = 1
                    # Loop over all the bits in the slow control word
                    for idx in range(numBitsRequired):
                        bitwiseArray[idx] = ( (slowControlWordContent & bitMask) >> idx)
                        bitMask = bitMask << 1
                    
                    '''
                        INTEGER TYPE: SECOND LOOP
                    '''
                    
                    # Loop over this new list and chop each 32 bits into the encoded sequence
                    for idx in range(len(bitwiseArray)):
#                        ''' DEBUG INFO '''
#                        if dictKey == debugComparisonKey:
#                            print "idx=%3i, bitPosn=%2i, seqIdxTotal:%9X" % (idx, bitPosition%32, bitwiseArray[idx] << (bitPosition%32)),
#                            print " (%i << %2i) " % (bitwiseArray[idx], (bitPosition%32)),
#                            print "= %9X" % (bitwiseArray[idx] << (bitPosition%32)),
#                            print " encSeq[%3i] = %9X" % (wordPosition, encodedSequence[wordPosition])

                        # Add running total to sequence; Increment bitPosition and check wordPosition 
                        encodedSequence[wordPosition] = encodedSequence[wordPosition] | (bitwiseArray[idx] << (bitPosition % 32) )
                        bitPosition += 1
                        wordPosition = bitPosition / 32

        # Return the encoded sequence for this (partial) tree
        return encodedSequence

         
    def generateBitMask(self, numBits):
        '''
            Generates that bit mask to cover the number of bits supplied.
            
            I.e. numBits = 1; returns 1,    2 = > 3, 3 => 7, 4 = > 15
        '''
        
        sum = 0
        for idx in range(numBits):
            sum = sum | (1 << idx)
            
        return sum
    
    def displayDictionaryValues(self):
        '''
            Debug function, used to display the dictionary values
        '''
        if self.bDebug:
            print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
            for cmd in self.paramsDict:
                # Get dictionary key's values
                dictKey = self.getParamValue(cmd)
                
                print "dictKey: ", cmd,
                if len(cmd) < 12:
                    print "\t",
                print " \tpos'n: ", dictKey[1], "\t [",
                # Is the third variable a list or an integer?
                if isinstance(dictKey[2], types.ListType):
                    # it's a list
                    for idx in range(11):
                        if (idx < 5):
                            # Print the first five values
                            print dictKey[2][idx],
                        elif idx == 5:
                            print ", .., ",
                        else:
                            # Print the last five values
                            print dictKey[2][-1*(11-idx)],
    
                elif isinstance(dictKey[2], types.IntType):
                   # it's just an integer
                   print dictKey[2],
                else:
                    print "displayDictionaryValues() Error: dictKey[2] is neither a list nor an integer!"
    
                print "]"


import unittest
    
class SlowCtrlParamsTest(unittest.TestCase):
    '''
    Unit test class for SlowCtrlParams.
    '''

    
    def testStringParse(self):
        '''
            Tests that updating a parameter works as expected
        '''
        
        daqBiasIdx47 = 11
        daqBiasDefault = 31
        selfTestDecoderDefault = 7
        digitalControlIdx3 = 18

        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <self_test_decoder pixel="1" value="5"/>
                                <self_test_decoder_default value="%i"/>
                                <mux_decoder pixel="2" value="0"/>
                                <mux_decoder_default value="3"/>
                                <daq_bias index="46" value="%i"/>
                                <daq_bias_default value="%i"/>
                                <daq_bias index="2" value="0"/>
                                <digital_control index="3" value="18"/>
                                <spare_bits value="%i"/>
                            </lpd_slow_ctrl_sequence>
        ''' % (selfTestDecoderDefault, daqBiasIdx47, daqBiasDefault, digitalControlIdx3)

  
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        paramsObj.encode()

        # Display an excerp of each dictionary key's value:
        paramsObj.displayDictionaryValues()
  
        # Setup and compare the unit tests..        
        dictKey = "self_test_decoder_default"
        index = 0
        value = selfTestDecoderDefault
        
        # Expected encoded values
        expectedVals = [3, -1, value, [False, True, False]]
        # The actual values
        selfTestDecoderDefaultVals = paramsObj.getParamValue(dictKey)

#        print selfTestDecoderDefaultVals, "\n", expectedVals
        self.assertEqual(selfTestDecoderDefaultVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)
        
        # 'self_test_decoder'                    : [5, 3585, [-1] * 47],
        dictKey = 'self_test_decoder'
        index = 497 # 1
        value = 5
        
        expectedVals = [3, 1537, [selfTestDecoderDefault] * 512, [True, True, False]]
        expectedVals[2][index] = value
        
        self_test_decoderVals = paramsObj.getParamValue(dictKey)
        
#        print self_test_decoderVals, "\n", expectedVals
        self.assertEqual(self_test_decoderVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)
        

        # daq_bias_default
        dictKey = "daq_bias_default"
        index = 0
        value = daqBiasDefault
        
        expectedVals = [5, -1, value, [False, True, False]]
        
        daqBiasDefaultVals = paramsObj.getParamValue(dictKey)
        
#        print daqBiasDefaultVals, "\n", expectedVals
        self.assertEqual(daqBiasDefaultVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)
        
        # 'daq_bias'                    : [5, 3585, [-1] * 47],
        dictKey = 'daq_bias'
        index = 5
        value = daqBiasIdx47
        
        expectedVals = [5, 3585, [daqBiasDefault] * 47, [False, True, True]]
        expectedVals[2][21-1] = 0
        expectedVals[2][34-1] = value
        
        daq_biasVals = paramsObj.getParamValue(dictKey)

#        print daq_biasVals, "\n", expectedVals
        self.assertEqual(daq_biasVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)

        # 'digital_control'
        dictKey = 'digital_control'
        index = 3
        value = digitalControlIdx3
        
        expectedVals = [40, 3865, value, [False, True, True]]
        expectedVals[2] = value

        digitalControlVals = paramsObj.getParamValue(dictKey)
        
#        print digitalControlVals, "\n", expectedVals
        self.assertEqual(digitalControlVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)

    
    def testOutOfRangeKeyValueFails(self):
        '''
        Tests that updating a parameter will fail if value exceeds valid range
        '''

        # Strictly not necessary except for the class constructor requiring a XML file or string
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="testOutOfRangeKeyValueFails">
                                <self_test_decoder_default value="7"/>
                            </lpd_slow_ctrl_sequence>
        '''        
        # setParamValue(dictKey, index, value)
        dictKey = "self_test_decoder_default"
        index = 0
        value = 8
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "self_test_decoder"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "mux_decoder_default"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "mux_decoder"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)
        
        # Test 1 bit widths
        dictKey = "feedback_select_default"
        value = 2
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "feedback_select"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "self_test_enable"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        # Test 5 bit widths
        dictKey = "daq_bias_default"
        value = 32
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "daq_bias"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        dictKey = "spare_bits"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        # Test 20 bit width
        dictKey = "filter_control"
        value = 1048575+1
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)
        
        dictKey = "adc_clock_delay"
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)

        # Test 40 bit width
        dictKey = "digital_control"
        value = 1099511627776
        with self.assertRaises(SlowCtrlParamsInvalidRangeError):
            paramsObj.setParamValue(dictKey, index, value)
    
    def testSelfTestDecoderDefaultSetValueSeven(self):
        '''
            Test that the key self_test_decoder_default works
        '''
            
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <self_test_decoder_default value="7"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # Display an excerp of each dictionary key's value:
        paramsObj.displayDictionaryValues()        

        # Construct a list of how sequence should look like
        expectedSequence = [0] * SlowCtrlParams.SEQLENGTH
        for idx in range(48,112):
            expectedSequence[idx] = 0xEEEEEEEE

        # Toggle display of debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            self.displaySequence(encSeq)

            print "\nExpected Sequence: (len)", len(expectedSequence)
            self.displaySequence(expectedSequence)

        self.assertEqual(encSeq, expectedSequence, 'testSelfTestDecoderDefaultSetValueSeven() failed !')
    
    
    def testFeedbackSelectDefaultSetValueOne(self):
        '''
            Test that the key feedback_select_default works
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <feedback_select_default value="1"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * SlowCtrlParams.SEQLENGTH
        for idx in range(48,112):
            expectedSequence[idx] = 0x11111111
        
        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            self.displaySequence(encSeq)

            print "\nExpected Sequence: (len)", len(expectedSequence)
            self.displaySequence(expectedSequence)
        
        self.assertEqual(encSeq, expectedSequence, 'testFeedbackSelectDefaultSetValueOne() failed !')
    
    def testFeedbackSelectAndSelfTestDecoderDefaultsCombined(self):
        '''
            Test that the keys feedback_select_default and self_test_decoder_default work together
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <feedback_select_default value="1"/>
                                <self_test_decoder_default value="2"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * SlowCtrlParams.SEQLENGTH
        for idx in range(48,112):
            expectedSequence[idx] = 0x55555555
        
        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            self.displaySequence(encSeq)

            print "\nExpected Sequence: (len)", len(expectedSequence)
            self.displaySequence(expectedSequence)
        
        self.assertEqual(encSeq, expectedSequence, 'testFeedbackSelectAndSelfTestDecoderDefaultsCombined() failed !')

    def testMuxDecoderDefault(self):
        '''
            Test that the key mux_decoder_default works
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <mux_decoder_default value="5"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * SlowCtrlParams.SEQLENGTH
        for idx in range(48):
            indexNo = idx % 3
            if indexNo == 0:
                expectedSequence[idx] = 0x6DB6DB6D
            elif indexNo == 1:
                expectedSequence[idx] = 0xDB6DB6DB
            else:
                expectedSequence[idx] = 0xB6DB6DB6
        
        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            self.displaySequence(encSeq)

            print "\nExpected Sequence: (len)", len(expectedSequence)
            self.displaySequence(expectedSequence)

        self.assertEqual(encSeq, expectedSequence, 'testMuxDecoderDefault() failed !')

    
    def testDaqBiasDefault(self):
        '''
            Test that the key daq_bias_default works
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <daq_bias_default value="1"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * SlowCtrlParams.SEQLENGTH
        expectedSequence[112] = 0x84210842
        expectedSequence[113] = 0x21084210
        expectedSequence[114] = 0x8421084
        expectedSequence[115] = 0x42108421
        expectedSequence[116] = 0x10842108
        expectedSequence[117] = 0x84210842
        expectedSequence[118] = 0x21084210
        expectedSequence[119] = 0x84
        
        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            self.displaySequence(encSeq)
            
            print "\nExpected Sequence: (len)", len(expectedSequence)
            self.displaySequence(expectedSequence)
            
        self.assertEqual(encSeq, expectedSequence, 'testDaqBiasDefault() (value = 1) failed !')


        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <daq_bias_default value="31"/>
                            </lpd_slow_ctrl_sequence>
        '''

        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()
            
        # How the sequence should end up looking
        expectedSequence = [0] * SlowCtrlParams.SEQLENGTH
        expectedSequence[112] = 0xFFFFFFFE
        expectedSequence[113] = 0xFFFFFFFF
        expectedSequence[114] = 0xFFFFFFFF
        expectedSequence[115] = 0xFFFFFFFF
        expectedSequence[116] = 0xFFFFFFFF
        expectedSequence[117] = 0xFFFFFFFF
        expectedSequence[118] = 0xFFFFFFFF
        expectedSequence[119] = 0xFFF

        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            self.displaySequence(encSeq)
            
            print "\nExpected Sequence: (len)", len(expectedSequence)
            self.displaySequence(expectedSequence)
            
        self.assertEqual(encSeq, expectedSequence, 'testDaqBiasDefault() (value = 31) failed !')
    
    def testSelfTestEnable(self):
        '''
            Test that the key self_test_enable works
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <self_test_enable value="1"/>
                            </lpd_slow_ctrl_sequence>
        '''

        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * SlowCtrlParams.SEQLENGTH
        expectedSequence[112] = 0x1

        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            self.displaySequence(encSeq)
            
            print "\nExpected Sequence: (len)", len(expectedSequence)
            self.displaySequence(expectedSequence)
        
        self.assertEqual(encSeq, expectedSequence, 'testSelfTestEnable() failed !')
    
    def testSpareBits(self):
        '''
            Test that the key spare_bits works
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <spare_bits value="31"/>
                            </lpd_slow_ctrl_sequence>
        '''
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * SlowCtrlParams.SEQLENGTH
        # 3820 / 32 = 119; 3820 % 32 = 12
        expectedSequence[119] = 31 << 12
        
        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            self.displaySequence(encSeq)
            
            print "\nExpected Sequence: (len)", len(expectedSequence)
            self.displaySequence(expectedSequence)
            
        self.assertEqual(encSeq, expectedSequence, 'testSpareBits() failed !')

    
    def testFilterControl(self):
        '''
            Test that the key filter_control works
        '''
        
        filterValue = 1048575
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <filter_control value="%i"/>
                            </lpd_slow_ctrl_sequence>
        ''' % filterValue
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        thisIndex = paramsObj.generateBitMask(15)
        
        overflow = ( filterValue >> (32 - 17))

        # How the sequence should end up looking
        expectedSequence = [0] * SlowCtrlParams.SEQLENGTH
        # 3825 / 32 = 119; 3825 % 32 = 17
        expectedSequence[119] = ( (filterValue & thisIndex) << 17)
        expectedSequence[120] = overflow

        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            self.displaySequence(encSeq)
            
            print "\nExpected Sequence: (len)", len(expectedSequence)
            self.displaySequence(expectedSequence)
        
        self.assertEqual(encSeq, expectedSequence, 'testFilterControl() failed !')
    
    def testAllKeysAllValues(self):
        '''
            Test all the keys
        '''
        
        daq_biasValue = 31
        filterValue = 0xFFFFF
        adcValue = filterValue
        digitalControlValue = 0xFFFFFFFFFF
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <mux_decoder_default value="7"/>
                                <feedback_select_default value="1"/>
                                <self_test_decoder_default value="7"/>
                                <self_test_enable value="1"/>
                                <daq_bias_default value="%i"/>
                                <spare_bits value="31"/>
                                <filter_control value="%i"/>
                                <adc_clock_delay value="%i"/>
                                <digital_control value="%i"/>
                            </lpd_slow_ctrl_sequence>
        ''' % (daq_biasValue, filterValue, adcValue, digitalControlValue)

        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0xFFFFFFFF] * SlowCtrlParams.SEQLENGTH
        expectedSequence[SlowCtrlParams.SEQLENGTH-1] = 1

        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            self.displaySequence(encSeq)

            print "\nExpected Sequence: (len)", len(expectedSequence)
            self.displaySequence(expectedSequence)

        self.assertEqual(encSeq, expectedSequence, 'testAllKeysAllValues() failed !')
    
    def testSpecificMuxDecoderValues(self):
        '''
            Test all the keys
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <mux_decoder pixel="511" value="5"/>
                                <mux_decoder pixel="479" value="1"/>
                                <mux_decoder pixel="447" value="1"/>
                                <mux_decoder pixel="415" value="1"/>
                                <mux_decoder pixel="0" value="1"/>
                                <mux_decoder pixel="32" value="1"/>
                                <mux_decoder pixel="64" value="1"/>
                                <mux_decoder pixel="96" value="1"/>
                                <mux_decoder_default value="7"/>
                            </lpd_slow_ctrl_sequence>
        '''

    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()


        # How the sequence should end up looking
        expectedSequence = [0] * SlowCtrlParams.SEQLENGTH
        for idx in range(48):
            expectedSequence[idx] = 0xFFFFFFFF
        expectedSequence[0] =  0xFFFFF24D
        expectedSequence[47] = 0x249FFFFF

        # Toggle display debug information
        if False:
            print "\n\nEncoded Sequence: (len)", len(encSeq)
            self.displaySequence(encSeq)

            print "\nExpected Sequence: (len)", len(expectedSequence)
            self.displaySequence(expectedSequence)

        self.assertEqual(encSeq, expectedSequence, 'testSpecificMuxDecoderValues() failed !')

    def displaySequence(self, seq):
        '''
            Helper function for unit testing, displays the contents of argument 'seq' sequence 
        '''
            
        for idx in range(len(seq)):
            if (idx % 8 == 0):
                print "\n%3i: " % idx,
            print "%9X" % seq[idx],
        print "\n"
        
        

if __name__ == '__main__':
    
    # Execute unit testing
    unittest.main()
    
    sys.exit()
    ''' Manual testing '''
    theParams = SlowCtrlParams('sampleSlowControl.xml', fromFile=True)
#    theParams = SlowCtrlParams('simple.xml', fromFile=True)
    
#    theParams.getParamValue("mux_decoder_default")
    width, posn, val, tags = theParams.getParamValue("mux_decoder_default")
#    print "Before: ", width, posn, val, "...", 
    
#    print "Changing self_test_decoder_default.."
#    theParams.setParamValue("mux_decoder_default", 1, 3)
     
#    width, posn, val = theParams.getParamValue("mux_decoder_default")
#    print "After: ", width, posn, val

    theElement = "mux_decoder_default"
    print "\n"
    
    theParams.displayDictionaryValues()
    
    ''' Encode XML file into dictionary '''
    result = theParams.encode()

    theParams.displayDictionaryValues()
