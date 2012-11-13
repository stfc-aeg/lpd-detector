# Check in setParaValue() for list/integer type 
import types, sys, os

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
#    biasCtrlLookupTable = [ 47, 46, 21, 15,  9, 36, 45, 19, 14,  8, 44, 
#                            32, 18, 12,  5, 43, 30, 17, 11,  2, 42, 24, 
#                            16, 10,  1, 41, 37, 28, 23,  7, 35, 33, 27, 
#                            22,  6, 40, 31, 26, 20,  4, 39, 29, 25, 13, 
#                             3, 38, 34]
    biasCtrlLookupTable = [ 24,  19,  44,  39,  14,  34,  29,   9,   4,  23,  18,  13,  43,   8,   3,  22, 
                            17,  12,   7,  38,   2,  33,  28,  21,  42,  37,  32,  27,  41,  16,  36,  11, 
                            31,  46,  30,   5,  26,  45,  40,  35,  25,  20,  15,  10,   6,   1,   0, ]

#    muxDecoderLookupTable = [512, 496, 480, 464, 448, 432, 416, 400, 
#                             384, 368, 352, 336, 320, 304, 288, 272, 
#                             256, 240, 224, 208, 192, 176, 160, 144, 
#                             128, 112,  96,  80,  64,  48,  32,  16, 
#                             511, 495, 479, 463, 447, 431, 415, 399, 
#                             383, 367, 351, 335, 319, 303, 287, 271, 
#                             255, 239, 223, 207, 191, 175, 159, 143, 
#                             127, 111,  95,  79,  63,  47,  31,  15, 
#                             510, 494, 478, 462, 446, 430, 414, 398, 
#                             382, 366, 350, 334, 318, 302, 286, 270, 
#                             254, 238, 222, 206, 190, 174, 158, 142, 
#                             126, 110,  94,  78,  62,  46,  30,  14, 
#                             509, 493, 477, 461, 445, 429, 413, 397, 
#                             381, 365, 349, 333, 317, 301, 285, 269, 
#                             253, 237, 221, 205, 189, 173, 157, 141, 
#                             125, 109,  93,  77,  61,  45,  29,  13, 
#                             508, 492, 476, 460, 444, 428, 412, 396, 
#                             380, 364, 348, 332, 316, 300, 284, 268, 
#                             252, 236, 220, 204, 188, 172, 156, 140, 
#                             124, 108,  92,  76,  60,  44,  28,  12, 
#                             507, 491, 475, 459, 443, 427, 411, 395, 
#                             379, 363, 347, 331, 315, 299, 283, 267, 
#                             251, 235, 219, 203, 187, 171, 155, 139, 
#                             123, 107,  91,  75,  59,  43,  27,  11, 
#                             506, 490, 474, 458, 442, 426, 410, 394, 
#                             378, 362, 346, 330, 314, 298, 282, 266, 
#                             250, 234, 218, 202, 186, 170, 154, 138, 
#                             122, 106,  90,  74,  58,  42,  26,  10, 
#                             505, 489, 473, 457, 441, 425, 409, 393, 
#                             377, 361, 345, 329, 313, 297, 281, 265, 
#                             249, 233, 217, 201, 185, 169, 153, 137, 
#                             121, 105,  89,  73,  57,  41,  25,   9,
#                             504, 488, 472, 456, 440, 424, 408, 392, 
#                             376, 360, 344, 328, 312, 296, 280, 264, 
#                             248, 232, 216, 200, 184, 168, 152, 136, 
#                             120, 104,  88,  72,  56,  40,  24,   8, 
#                             503, 487, 471, 455, 439, 423, 407, 391, 
#                             375, 359, 343, 327, 311, 295, 279, 263, 
#                             247, 231, 215, 199, 183, 167, 151, 135, 
#                             119, 103,  87,  71,  55,  39,  23,   7, 
#                             502, 486, 470, 454, 438, 422, 406, 390, 
#                             374, 358, 342, 326, 310, 294, 278, 262, 
#                             246, 230, 214, 198, 182, 166, 150, 134, 
#                             118, 102,  86,  70,  54,  38,  22,   6, 
#                             501, 485, 469, 453, 437, 421, 405, 389, 
#                             373, 357, 341, 325, 309, 293, 277, 261, 
#                             245, 229, 213, 197, 181, 165, 149, 133, 
#                             117, 101,  85,  69,  53,  37,  21,   5,
#                             500, 484, 468, 452, 436, 420, 404, 388, 
#                             372, 356, 340, 324, 308, 292, 276, 260, 
#                             244, 228, 212, 196, 180, 164, 148, 132, 
#                             116, 100,  84,  68,  52,  36,  20,   4, 
#                             499, 483, 467, 451, 435, 419, 403, 387, 
#                             371, 355, 339, 323, 307, 291, 275, 259, 
#                             243, 227, 211, 195, 179, 163, 147, 131, 
#                             115,  99,  83,  67,  51,  35,  19,   3, 
#                             498, 482, 466, 450, 434, 418, 402, 386, 
#                             370, 354, 338, 322, 306, 290, 274, 258, 
#                             242, 226, 210, 194, 178, 162, 146, 130, 
#                             114,  98,  82,  66,  50,  34,  18,   2, 
#                             497, 481, 465, 449, 433, 417, 401, 385, 
#                             369, 353, 337, 321, 305, 289, 273, 257, 
#                             241, 225, 209, 193, 177, 161, 145, 129, 
#                             113,  97,  81,  65,  49,  33,  17,   1 ]
    muxDecoderLookupTable = [512, 480, 448, 416, 384, 352, 320, 288, 256, 224, 192, 160, 128,  96,  64,  32, 
                            511, 479, 447, 415, 383, 351, 319, 287, 255, 223, 191, 159, 127,  95,  63,  31, 
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
                            481, 449, 417, 385, 353, 321, 289, 257, 225, 193, 161, 129,  97,  65,  33,   1, ]
    
#    pixelSelfTestLookupTable = [497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 
#                                496, 495, 494, 493, 492, 491, 490, 489, 488, 487, 486, 485, 484, 483, 482, 481, 
#                                465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 
#                                464, 463, 462, 461, 460, 459, 458, 457, 456, 455, 454, 453, 452, 451, 450, 449, 
#                                433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 
#                                432, 431, 430, 429, 428, 427, 426, 425, 424, 423, 422, 421, 420, 419, 418, 417, 
#                                401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 
#                                400, 399, 398, 397, 396, 395, 394, 393, 392, 391, 390, 389, 388, 387, 386, 385, 
#                                369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 
#                                368, 367, 366, 365, 364, 363, 362, 361, 360, 359, 358, 357, 356, 355, 354, 353, 
#                                337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 
#                                336, 335, 334, 333, 332, 331, 330, 329, 328, 327, 326, 325, 324, 323, 322, 321, 
#                                305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 
#                                304, 303, 302, 301, 300, 299, 298, 297, 296, 295, 294, 293, 292, 291, 290, 289, 
#                                273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 
#                                272, 271, 270, 269, 268, 267, 266, 265, 264, 263, 262, 261, 260, 259, 258, 257, 
#                                241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 
#                                240, 239, 238, 237, 236, 235, 234, 233, 232, 231, 230, 229, 228, 227, 226, 225, 
#                                209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 
#                                208, 207, 206, 205, 204, 203, 202, 201, 200, 199, 198, 197, 196, 195, 194, 193, 
#                                177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 
#                                176, 175, 174, 173, 172, 171, 170, 169, 168, 167, 166, 165, 164, 163, 162, 161, 
#                                145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 
#                                144, 143, 142, 141, 140, 139, 138, 137, 136, 135, 134, 133, 132, 131, 130, 129, 
#                                113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 
#                                112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100,  99,  98,  97, 
#                                 81,  82,  83,  84,  85,  86,  87,  88,  89,  90,  91,  92,  93,  94,  95,  96, 
#                                 80,  79,  78,  77,  76,  75,  74,  73,  72,  71,  70,  69,  68,  67,  66,  65, 
#                                 49,  50,  51,  52,  53,  54,  55,  56,  57,  58,  59,  60,  61,  62,  63,  64, 
#                                 48,  47,  46,  45,  44,  43,  42,  41,  40,  39,  38,  37,  36,  35,  34,  33, 
#                                 17,  18,  19,  20,  21,  22,  23,  24,  25,  26,  27,  28,  29,  30,  31,  32, 
#                                 16,  15,  14,  13,  12,  11,  10,   9,   8,   7,   6,   5,   4,   3,   2,   1, ]

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

    def __init__(self, xmlObject, fromFile=False, strict=True):
        #TODO: Sort out argument list - will have implications wherever objects are created of this class
        strict = True
        # Set the strict syntax flag to specified value (defaults to true)
        self.strict = strict
        
        ''' Debug info: '''
        self.bDebug = False

        if self.bDebug:
            print "debugging enabled."

        #    paramsDict = {'dictKey'                     : [width, posn, value(s), skip, [bPixelTagRequired, bValueTagRequired, bIndexTagRequired]}
        self.paramsDict = {'mux_decoder_default'         : [3,  -1,     -1,         0, [False, True, False]],
                           'mux_decoder'                 : [3,  0,      [-1] * 512, 0, [True,  True, False]],
                           'feedback_select_default'     : [1,  -1,     -1,         0, [False, True, False]],
                           'feedback_select'             : [1,  1536,   [-1] * 512, 3, [True,  True, False]],
                           'self_test_decoder_default'   : [3,  -1,     -1,         0, [False, True, False]],
                           'self_test_decoder'           : [3,  1537,   [-1] * 512, 1, [True,  True, False]],
                           'self_test_enable'            : [1,  3584,   -1,         0, [False, True, False]],
                           'daq_bias_default'            : [5,  -1,     -1,         0, [False, True, False]],
                           'daq_bias'                    : [5,  3585,   [-1] * 47,  0, [False, True, True]],
                           'spare_bits'                  : [5,  3820,   -1,         0, [False, True, False]],       # Special Case: 5 bits cover everything
                           'filter_control'              : [20, 3825,   -1,         0, [False, True, False]],       # Special Case: 20 bits cover everything
                           'adc_clock_delay'             : [20, 3845,   -1,         0, [False, True, False]],       # Special Case: 20 bits cover everything
                           'digital_control'             : [40, 3865,   -1,         0, [False, True, False]],       # Special Case: 40 bits cover everything
                           }

        
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
            skip = result[3]
            tags = result[4]
        else:
            print "\"" + dictKey + "\" doesn't exist."
        
        return [width, posn, val, skip, tags]
 
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
            Accepts the dictionary key 'dictKey' and associated index 'idx' and performs the dictionary lookup for the four different keys that have a dictionary lookup table.
            
            'idx' returned unchanged for the other keys.
        '''

#        return idx

        # Does dictKey have an associated lookup table?
        if dictKey == "mux_decoder":
            return (SlowCtrlParams.muxDecoderLookupTable[idx] - 1)
        elif dictKey == "feedback_select":
            return (SlowCtrlParams.pixelSelfTestLookupTable[idx] - 1)
        elif dictKey == "self_test_decoder":
            return (SlowCtrlParams.pixelSelfTestLookupTable[idx] - 1)
        elif dictKey == "daq_bias":
            return SlowCtrlParams.biasCtrlLookupTable[idx]
#            return (SlowCtrlParams.biasCtrlLookupTable[idx] - 1)
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

        # The structure of the parameters dictionary is:
        # paramsDict = {'dictKey' : [width, posn, value(s), [bPixelTagRequired, bValueTagRequired, bIndexTagRequired]}
        #     where values(s) is an integer or a list, and the nested list of booleans defines which tags that are required

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
                bPixel = pmValues[4][0]
                bValue = pmValues[4][1]
                bIndex = pmValues[4][2]
                
                # Get value attribute (always present)
                value = self.getAttrib(child, 'value')
                if value == -2:
                    # Fail if there is no value present
                    raise SlowCtrlParamsError("Unable to find the required 'value' tag for key '%s'!" % cmd)
                
                if self.bDebug:
                    print "value = ", value,
                
                # Is there a pixel tag?
                if bPixel:
                    # Get pixel
                    pixel = self.getAttrib(child, 'pixel')
                    
                    # Use pixel number to obtain pixel order using the lookup table function
                    orderedPxl = self.doLookupTableCheck(cmd, pixel)
                    
                    if self.bDebug:
                        print " pixel, orderedPxl = %3i, %3i" % (pixel, orderedPxl),
                    # Update pixel entry of the dictionary key
                    self.setParamValue(cmd, orderedPxl, value)

                else:
                    # No pixel; Is there an index tag?
                    if bIndex:
                        index = self.getAttrib(child, 'index')
                        
                        # Use index to obtain index order using the lookup table function
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
            

        # Pass through XXX_default keys and change their value from -1 to 0 unless already set
        for key in self.paramsDict:
            # Is this a XXX_default key?
            if key.endswith("_default"):
                if self.bDebug:
                    print "1st Pass: Found _default key: ", key, " = ",

                # Obtain _default's value
                defaultKeyValue = self.getParamValue(key)
                if self.bDebug:
                    print defaultKeyValue,

                # Is XXX_default's value not specified ?
                if defaultKeyValue[2] == -1:
                    # Default not set; set it's value to 0
                    self.setParamValue(key, 0, 0)
                    if self.bDebug:
                        print " now = ", self.getParamValue(key)[2]
                else:
                    if self.bDebug:
                        print " (no change)"
                    

        if self.bDebug:
            print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
        
        # Check _default keys and updated the corresponding keys unless where the associated keys have explicitly set value(s)
        #    e.g. if daq_bias_default = 4 them all values of daq_bias will become 4 (unless set explicitly)

        for key in self.paramsDict:
            # Is this a XXX_default key?
            if key.endswith("_default"):

                if self.bDebug:
                    print "2nd Pass: Found _default key: ", key, " = ",

                # Obtain key value
                defaultKeyValue = self.getParamValue(key)
                if self.bDebug:
                    print defaultKeyValue
                
                # Derive corresponding key's name
                #    e.g. key = "mux_decoder_default"; sectionKey = "mux_decoder"
                sectionKey = key.replace("_default", "")
                sectionKeyValue = self.getParamValue(sectionKey)
                sectionKeyLength = len(sectionKeyValue[2])

                # Updates all values of the key except any that have already been explicitly set
                for idx in range(sectionKeyLength):
                    # Update only if value not explicitly set
                    if sectionKeyValue[2][idx] == -1:
                        # -1 denotes value hasn't been explicitly set; go ahead and update it
                        self.setParamValue(sectionKey, idx, defaultKeyValue[2])
            else:
                # All keys that does not end with "_default", and that does not contain a list of values
                #    eg:
                #        self_test_enable, spare_bits, filter_control, adc_clock_delay, digital_control

                keyValue = self.getParamValue(key)

                if isinstance(keyValue[2], types.IntType):
                    if self.bDebug:
                        print "%21s: It's an integer type" % key
                    
                    # Has the value been set already?
                    if keyValue[2] == -1:
                        # Not set; Set it to 0
                        self.setParamValue(key, 0, 0)
                    
        # Back up one level in the tree              
        self.depth = self.depth - 1

        
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
        debugComparisonKey = ""
#        debugComparisonKey = "spare_bits"
#        debugComparisonKey = "feedback_select"  
#        debugComparisonKey = "mux_decoder"
#        debugComparisonKey = "daq_bias" 
#        debugComparisonKey = "self_test_decoder"
#        debugComparisonKey = "digital_control"

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
                # Word width (number of bits) of this key?
                keyWidth = cmdParams[0]
                # Where does current key reside within the sequence?
                wordPosition = cmdParams[1] / 32
                # Slow Control Value(s)
                slowControlWordContent = cmdParams[2]
                # bitPosition tracks the current bit position relative to the entire length of sequence (0 - 3904)
                bitPosition = cmdParams[1]
                # Skip - distance between two slow control words within  the same section
                wordSkip = cmdParams[3]
                
                # Is this a list?
                if isinstance(slowControlWordContent, types.ListType):

                    # Determine number of entries in the nested list
                    numBitsRequired = len(slowControlWordContent)

                    # Create a bit array to save all the slow control words, bit by bit
                    bitwiseArray = [0] * 3905

                    ''' 
                        LIST TYPE: FIRST LOOP
                    '''
#                    if dictKey == debugComparisonKey:
#                        print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n     LIST TYPE: FIRST LOOP "
#                        print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\ndictKey:%15s       len(bitwiseArray): %4i" % (dictKey, len(bitwiseArray))
#                    indexMax = len(bitwiseArray) - 1
                    # Loop over all the elements of the nested list and produce bitwiseArray (MSB first)
                    #    e.g.: if keyWidth = 3, list = [1, 3, 6, .] then bitwiseOffset = [ (0, 0, 1,) (0, 1, 1,) (1, 1, 0,) ..]
                    for idx in range(numBitsRequired):


                        ''' SORT BIT ORDER !  '''
                        bitMask = 2**(keyWidth-1)
                        # Iterate over each slow control word for the current key
                        for scIdx in range(keyWidth):

                            # bitShiftOffset determines number of bits to shift within current slow control word
                            bitShiftOffset = (keyWidth-1) - scIdx

#                            ''' DEBUG INFO '''
#                            if dictKey == debugComparisonKey:
#                                if idx < 5:
#                                    if scIdx < keyWidth:#                                                                                                                    # bitwiseArray[%4i + %2i + %2i + %4i] =
#                                        print "bitwiseArray[%4i + %2i + %2i + %4i] = ( (scWordContent[%3i] & %2i) >> %4i) => b..[%4i] = ( (%4X & %2i) >> %2X)   =   %2i." % (bitPosition, keyWidth*idx, scIdx, wordSkip*idx,
#                                                                                                                                                                             # (scWordContent[%3i] & %2i) >> %4i
#                                                                                                                                                                             idx, bitMask, bitShiftOffset,
#                                                                                                                                                                             #  b..[%4i] = 
#                                                                                                                                                                             bitPosition + keyWidth*idx + scIdx + wordSkip*idx,
#                                                                                                                                                                             # ( (%4X & %2i) >> %2X)   = 
#                                                                                                                                                                             slowControlWordContent[idx], bitMask, bitShiftOffset,
#                                                                                                                                                                             # %2i."
#                                                                                                                                                                             ( (slowControlWordContent[idx] & bitMask) >> bitShiftOffset)
#                                                                                                                                                                             )
                            #bitMask = 1 << scIdx
                            bitwiseArray[bitPosition + keyWidth*idx + scIdx + wordSkip*idx] = ( (slowControlWordContent[idx] & bitMask) >> bitShiftOffset)
                            bitMask = bitMask >> 1

#                    ''' DEBUG INFO '''
#                    if dictKey == debugComparisonKey:
#                        if dictKey == "feedback_select":
#                            specialCase = 3
#                        elif dictKey == "self_test_decoder":
#                            specialCase = 1
#                        else:
#                            specialCase = 0
#                        outputWidth = (40/keyWidth) * keyWidth
#                        lowerLimit = bitPosition - (bitPosition % outputWidth)
#                        upperLimit = bitPosition + numBitsRequired*(keyWidth+ specialCase)
##                        print "bitPosition + numBitsRequired*(keyWidth+ specialCase)   == >   %3i + %3i * (%2i+ %i) " % (bitPosition, numBitsRequired, keyWidth, specialCase)
#                        print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n%15s       len(bitwiseArray): %4i, content: " % (dictKey, len(bitwiseArray)),
#                        for idx in range( len(bitwiseArray) ):
#                            if idx < lowerLimit:
#                                continue
#                            if idx > upperLimit:
#                                continue
#                            if (idx % (outputWidth)) == 0:
#                                print "\n%4i: " % idx,
#                            print "%2i" % bitwiseArray[ idx ],
#                        print ""

                    '''
                        LIST TYPE: SECOND LOOP
                    '''
#                    if dictKey == debugComparisonKey:
#                        print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n     LIST TYPE: SECOND LOOP "
                        
                    # Loop over the bitwiseArray in reverse order and copy 32 bits at a time into the encoded sequence
                    for idx in range( len(bitwiseArray) ): #for idx in range( len(bitwiseArray)-1, -1, -1):

                        # Determine location inside sequence; Determine relative position within current index (from MSB to LSB)
                        wordPosition = idx / 32
                        bitOffset = idx % 32
                        
#                        ''' DEBUG INFO '''
#                        if dictKey == debugComparisonKey:
#                            if idx < 33:#if idx > 3865:
#                                pass#print "idx, bit-Value, wordPosition, bitOffset = %3i, %1i, %3i, %2X" % (idx, bitwiseArray[idx], wordPosition, bitOffset)

                        # Add running total to sequence; increment bitPosition and check wordPosition 
                        try:
                            encodedSequence[wordPosition] = encodedSequence[wordPosition] | (bitwiseArray[idx] << bitOffset)
                        except:
                            print "(LIST)   BANG! Key '%s' wordPosition = %i, idx = %i, bitwise sum = %i\n" % (dictKey, wordPosition, idx, (bitwiseArray[idx] << bitOffset) )
                            return

                else:
                    
                    '''
                        INTEGER TYPE
                    '''
                    # Split the integer into bitwise array

                    # Need not update encoded sequence if slow control word empty
                    if slowControlWordContent == 0:
                        continue

                    # How many bits to use
                    numBitsRequired = cmdParams[0]
                    # Create a bit array to save each bit individually from the slow control word
                    bitwiseArray = [0] * numBitsRequired                    
                    
                    '''
                        INTEGER TYPE: FIRST LOOP
                    '''

                    if dictKey == debugComparisonKey:
                        print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
                        print "   %s" % dictKey, " First Loop (Building bitwiseArray)"

                    bitMask = 2**(keyWidth-1)
                    # Loop over all the bits in the slow control word
                    for idx in range(numBitsRequired):

                        # bitShiftOffset determines number of bits to shift within current slow control word
                        bitShiftOffset = (keyWidth-1) - idx

                        ''' DEBUG INFO '''
                        if dictKey == debugComparisonKey:
                            if idx < keyWidth:#                                                  # bitwiseArray[%4i] =
                                print "bitwiseArray[%4i] = ( (%5i & %2i) >> %4i) =>     %2i." % (idx,
                                                                                                 # (%5i & %2i) >> %4i
                                                                                                 slowControlWordContent, bitMask, bitShiftOffset,
                                                                                                 # %2i."
                                                                                                 ( (slowControlWordContent & bitMask) >> bitShiftOffset)
                                                                                                 )


                        # bitShiftOffset determines number of bits to shift with current slow control word (from MSB to LSB)
                        bitwiseArray[ idx ] = ( (slowControlWordContent & bitMask) >> bitShiftOffset)
                        bitMask = bitMask >> 1
                        
#                        bitwiseArray[ indexMax - idx ] = ( (slowControlWordContent & bitMask) >> idx)
#                        bitMask = bitMask << 1
                    
                    '''
                        INTEGER TYPE: SECOND LOOP
                    '''
                    if dictKey == debugComparisonKey:
                        print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
                        print "   %s" % dictKey, " Second Loop (Copying bitwiseArray into sequence)"
                    
                    # Loop over this new list and copy into the encoded sequence
                    for idx in range(len(bitwiseArray)):

                        wordPosition = (cmdParams[1] + idx) / 32
                        bitOffset = (cmdParams[1] + idx) % 32

                        ''' DEBUG INFO '''
                        if dictKey == debugComparisonKey:
                            print "(idx=%2i) encSq[%3i] = encSeq[%3i] | (bwArray[%2i] << (%2i))  =>   %8X | (%2i << %2i)  =>  %8X | (%8X)   =   %8X" % (idx, wordPosition, wordPosition, idx, bitOffset, 
                                                                                                                                         # %8X | (%2i << %2i)
                                                                                                                                         encodedSequence[idx], bitwiseArray[idx], bitOffset,
                                                                                                                                         # =>  %8X | (% %8X)
                                                                                                                                         encodedSequence[idx], (bitwiseArray[idx] << bitOffset),
                                                                                                                                         encodedSequence[wordPosition] | (bitwiseArray[idx] << bitOffset)
                                                                                                                                         )                        

                        # Add running total to sequence; increment bitPosition and check wordPosition 
                        try:
                            encodedSequence[wordPosition] = encodedSequence[wordPosition] | (bitwiseArray[idx] << bitOffset)
                        except:
                            print "(integer!) BANG! Key '%s' wordPosition = %i, idx = %i, bitwise sum = %i\n" % (dictKey, wordPosition, idx, (bitwiseArray[idx] << bitOffset) )
                            print "key = %s" % dicKey
                            return
                        
                        # Add running total to sequence; Increment bitPosition and check wordPosition 
#                        encodedSequence[wordPosition] = encodedSequence[wordPosition] | (bitwiseArray[idx] << (31 - (bitPosition % 32)) )
#                        bitPosition += 1
#                        wordPosition = bitPosition / 32

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

    def fetchParamsDictionary(self):
        '''
            Utility function used by unit testing class to obtain dictionary values
        '''
        return self.paramsDict
    
import unittest
    
class SlowCtrlParamsTest(unittest.TestCase):
    '''
    Unit test class for SlowCtrlParams.
    '''


    def testStringParse(self):
        '''
            Tests that updating a parameter works as expected
        '''
        
        selfTestPixelIndex = 1
        daqBiasIdx47Value = 11
        daqBiasDefault = 31
        selfTestDecoderDefault = 7
        digitalControlIdx3 = 18

        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
                                <self_test_decoder pixel="%i" value="5"/>
                                <self_test_decoder_default value="%i"/>
                                <mux_decoder pixel="2" value="0"/>
                                <mux_decoder_default value="3"/>
                                
                                <daq_bias index="46" value="%i"/>
                                <daq_bias_default value="%i"/>
                                <daq_bias index="2" value="0"/>
                                
                                <digital_control value="18"/>
                                <spare_bits value="%i"/>
                            </lpd_slow_ctrl_sequence>
        ''' % (selfTestPixelIndex, selfTestDecoderDefault, daqBiasIdx47Value, daqBiasDefault, digitalControlIdx3)

  
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
#        expectedVals = [3, -1, value, 0, [False, True, False]]
        expectedVals = paramsObj.fetchParamsDictionary()['self_test_decoder_default']
        # The actual values
        selfTestDecoderDefaultVals = paramsObj.getParamValue(dictKey)

#        print "\n", selfTestDecoderDefaultVals, "\n", expectedVals
        self.assertEqual(selfTestDecoderDefaultVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)
        
        # 'self_test_decoder'                    : [5, 3585, [-1] * 47],
        dictKey = 'self_test_decoder'
        index = selfTestPixelIndex
        value = 5
        
        expectedVals = [3, 1537, [selfTestDecoderDefault] * 512, 1, [True, True, False]]
        expectedVals[2][ SlowCtrlParams.pixelSelfTestLookupTable[index] -1 ] = value

#        print "\n497: ", SlowCtrlParams.pixelSelfTestLookupTable[497]
        
        self_test_decoderVals = paramsObj.getParamValue(dictKey)
        
#        print "\n", self_test_decoderVals, "\n", expectedVals
        self.assertEqual(self_test_decoderVals[0], expectedVals[0], 'testStringParse() failed to update key \"%s\" as expected' % dictKey)
        

        # daq_bias_default
        dictKey = "daq_bias_default"
        index = 0
        value = daqBiasDefault
        
        expectedVals = [5, -1, value, 0, [False, True, False]]
        
        daqBiasDefaultVals = paramsObj.getParamValue(dictKey)
        
#        print "\n", daqBiasDefaultVals, "\n", expectedVals
        self.assertEqual(daqBiasDefaultVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)
        
        # 'daq_bias'                    : [5, 3585, [-1] * 47],
        dictKey = 'daq_bias'
        value = daqBiasIdx47Value
        
        expectedVals = [5, 3585, [daqBiasDefault] * 47, 0, [False, True, True]]

        expectedVals[2][ SlowCtrlParams.biasCtrlLookupTable[2] ] = 0
        expectedVals[2][ SlowCtrlParams.biasCtrlLookupTable[46] ] = value
        
        daq_biasVals = paramsObj.getParamValue(dictKey)

#        print "\nEnc: ", daq_biasVals, "\nExp: ", expectedVals
        self.assertEqual(daq_biasVals, expectedVals, 'testStringParse() failed to update key \"%s\" as expected' % dictKey)

        # 'digital_control'
        dictKey = 'digital_control'
        index = 3
        value = digitalControlIdx3
        
        expectedVals = [40, 3865, value, 0, [False, True, False]]
        expectedVals[2] = value

        digitalControlVals = paramsObj.getParamValue(dictKey)
        
#        print "\n", digitalControlVals, "\n", expectedVals
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
        expectedSequence[112] = 0x42108420
        expectedSequence[113] = 0x10842108
        expectedSequence[114] = 0x84210842
        expectedSequence[115] = 0x21084210
        expectedSequence[116] = 0x08421084
        expectedSequence[117] = 0x42108421
        expectedSequence[118] = 0x10842108
        expectedSequence[119] = 0x842
        
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
            Test a set of specific mux_decoder key values
        '''
        
        stringCmdXml = '''<?xml version="1.0"?>
                            <lpd_slow_ctrl_sequence name="TestString">
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
                            </lpd_slow_ctrl_sequence>
        '''
#                                <mux_decoder_default value="7"/>
    
        # Parse XML and encode
        paramsObj = SlowCtrlParams(stringCmdXml)
        encSeq = paramsObj.encode()

        # How the sequence should end up looking
        expectedSequence = [0] * SlowCtrlParams.SEQLENGTH
        for idx in range(48):
            expectedSequence[idx] = 0x0
        expectedSequence[0] =  0xF9AA6
        expectedSequence[1] =  0x30
        expectedSequence[2] =  0x4
        expectedSequence[47] = 0x40882000

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
#            if idx < 112:
#                continue
            if (idx % 8 == 0):
                print "\n%3i: " % idx,
            print "%9X" % seq[idx],
        print "\n"
        

if __name__ == '__main__':
    
    # Execute unit testing
    unittest.main()
    
    sys.exit()

    ''' 
        Manual testing - Turning the contents of the slow control file 
                         into a 32 bit word sequence and print it
                         
        'SlowControlMachined.xml' produced by the script: ExtractSlowControlParamsFromFile.py
    '''
#    thisFile = '/experimentation.xml'
#    thisFile = '/scParameters.xml'
    thisFile = '/SlowControlMachined.xml'
    currentDir = os.getcwd()
    if currentDir.endswith("LpdFemTests"):
        thisFile = currentDir + thisFile
    else:
        thisFile = currentDir + "/LpdFemTests" + thisFile

    theParams = SlowCtrlParams(thisFile, fromFile=True)
    encodedSequence = theParams.encode()

    print "Processing '%s' produces the sequence: " % thisFile
    for idx in range(len(encodedSequence)):
        if True: #idx > 103:
            if (idx % 8 == 0):
                print "\n%3i: " % idx,
            print "%9X" % encodedSequence[idx],
    print "\n"
    

    theParams.displayDictionaryValues()
