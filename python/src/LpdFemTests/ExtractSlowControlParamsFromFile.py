'''
Created on Aug 29, 2012

@author: ckd27546
'''

# Import Python standard modules
from string import strip, split
import os, sys

class ExtractSlowControlParamsFromFile():

    # Get path of current working directory
    currentDir = os.getcwd()
    if not currentDir.endswith("LpdFemTests"):
        currentDir += "/LpdFemTests"


    # Lookup tables for the various sections of the slow control configuration file
#    biasCtrlLookupTable = [47, 46, 21, 15, 9, 36, 45, 19, 14, 8, 44, 
#                        32, 18, 12, 5, 43, 30, 17, 11, 2, 42, 24, 
#                        16, 10, 1, 41, 37, 28, 23, 7, 35, 33, 27, 
#                        22, 6, 40, 31, 26, 20, 4, 39, 29, 25, 13, 
#                        3, 38, 34]

    biasCtrlLookupTable = [ 24,  19,  44,  39,  14,  34,  29,   9,   4,  23,  18,  13,  43,   8,   3,  22, 
                            17,  12,   7,  38,   2,  33,  28,  21,  42,  37,  32,  27,  41,  16,  36,  11, 
                            31,  46,  30,   5,  26,  45,  40,  35,  25,  20,  15,  10,   6,   1,   0, ]
    
#    muxDecoderLookupTable = [512, 496, 480, 464, 448, 432, 416, 
#                             400, 384, 368, 352, 336, 320, 304, 
#                             288, 272, 256, 240, 224, 208, 192, 
#                             176, 160, 144, 128, 112, 96, 80, 
#                             64, 48, 32, 16, 511, 495, 479, 
#                             463, 447, 431, 415, 399, 383, 367, 
#                             351, 335, 319, 303, 287, 271, 255, 
#                             239, 223, 207, 191, 175, 159, 143, 
#                             127, 111, 95, 79, 63, 47, 31, 
#                             15, 510, 494, 478, 462, 446, 430, 
#                             414, 398, 382, 366, 350, 334, 318, 
#                             302, 286, 270, 254, 238, 222, 206, 
#                             190, 174, 158, 142, 126, 110, 94, 
#                             78, 62, 46, 30, 14, 509, 493, 
#                             477, 461, 445, 429, 413, 397, 381, 
#                             365, 349, 333, 317, 301, 285, 269, 
#                             253, 237, 221, 205, 189, 173, 157, 
#                             141, 125, 109, 93, 77, 61, 45, 
#                             29, 13, 508, 492, 476, 460, 444, 
#                             428, 412, 396, 380, 364, 348, 332, 
#                             316, 300, 284, 268, 252, 236, 220, 
#                             204, 188, 172, 156, 140, 124, 108, 
#                             92, 76, 60, 44, 28, 12, 507, 
#                             491, 475, 459, 443, 427, 411, 395, 
#                             379, 363, 347, 331, 315, 299, 283, 
#                             267, 251, 235, 219, 203, 187, 171, 
#                             155, 139, 123, 107, 91, 75, 59, 
#                             43, 27, 11, 506, 490, 474, 458, 
#                             442, 426, 410, 394, 378, 362, 346, 
#                             330, 314, 298, 282, 266, 250, 234, 
#                             218, 202, 186, 170, 154, 138, 122, 
#                             106, 90, 74, 58, 42, 26, 10, 
#                             505, 489, 473, 457, 441, 425, 409, 
#                             393, 377, 361, 345, 329, 313, 297, 
#                             281, 265, 249, 233, 217, 201, 185, 
#                             169, 153, 137, 121, 105, 89, 73, 
#                             57, 41, 25, 9, 504, 488, 472, 
#                             456, 440, 424, 408, 392, 376, 360, 
#                             344, 328, 312, 296, 280, 264, 248, 
#                             232, 216, 200, 184, 168, 152, 136, 
#                             120, 104, 88, 72, 56, 40, 24, 
#                             8, 503, 487, 471, 455, 439, 423, 
#                             407, 391, 375, 359, 343, 327, 311, 
#                             295, 279, 263, 247, 231, 215, 199, 
#                             183, 167, 151, 135, 119, 103, 87, 
#                             71, 55, 39, 23, 7, 502, 486, 
#                             470, 454, 438, 422, 406, 390, 374, 
#                             358, 342, 326, 310, 294, 278, 262, 
#                             246, 230, 214, 198, 182, 166, 150, 
#                             134, 118, 102, 86, 70, 54, 38, 
#                             22, 6, 501, 485, 469, 453, 437, 
#                             421, 405, 389, 373, 357, 341, 325, 
#                             309, 293, 277, 261, 245, 229, 213, 
#                             197, 181, 165, 149, 133, 117, 101, 
#                             85, 69, 53, 37, 21, 5, 500, 
#                             484, 468, 452, 436, 420, 404, 388, 
#                             372, 356, 340, 324, 308, 292, 276, 
#                             260, 244, 228, 212, 196, 180, 164, 
#                             148, 132, 116, 100, 84, 68, 52, 
#                             36, 20, 4, 499, 483, 467, 451, 
#                             435, 419, 403, 387, 371, 355, 339, 
#                             323, 307, 291, 275, 259, 243, 227, 
#                             211, 195, 179, 163, 147, 131, 115, 
#                             99, 83, 67, 51, 35, 19, 3, 
#                             498, 482, 466, 450, 434, 418, 402, 
#                             386, 370, 354, 338, 322, 306, 290, 
#                             274, 258, 242, 226, 210, 194, 178, 
#                             162, 146, 130, 114, 98, 82, 66, 
#                             50, 34, 18, 2, 497, 481, 465, 
#                             449, 433, 417, 401, 385, 369, 353, 
#                             337, 321, 305, 289, 273, 257, 241, 
#                             225, 209, 193, 177, 161, 145, 129, 
#                             113, 97, 81, 65, 49, 33, 17, 
#                             1 ]

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

#    pixelSelfTestLookupTable = [497, 497, 498, 498, 499, 499, 500, 
#                                500, 501, 501, 502, 502, 503, 503, 
#                                504, 504, 505, 505, 506, 506, 507, 
#                                507, 508, 508, 509, 509, 510, 510, 
#                                511, 511, 512, 512, 496, 496, 495, 
#                                495, 494, 494, 493, 493, 492, 492, 
#                                491, 491, 490, 490, 489, 489, 488, 
#                                488, 487, 487, 486, 486, 485, 485, 
#                                484, 484, 483, 483, 482, 482, 481, 
#                                481, 465, 465, 466, 466, 467, 467, 
#                                468, 468, 469, 469, 470, 470, 471, 
#                                471, 472, 472, 473, 473, 474, 474, 
#                                475, 475, 476, 476, 477, 477, 478, 
#                                478, 479, 479, 480, 480, 464, 464, 
#                                463, 463, 462, 462, 461, 461, 460, 
#                                460, 459, 459, 458, 458, 457, 457, 
#                                456, 456, 455, 455, 454, 454, 453, 
#                                453, 452, 452, 451, 451, 450, 450, 
#                                449, 449, 433, 433, 434, 434, 435, 
#                                435, 436, 436, 437, 437, 438, 438, 
#                                439, 439, 440, 440, 441, 441, 442, 
#                                442, 443, 443, 444, 444, 445, 445, 
#                                446, 446, 447, 447, 448, 448, 432, 
#                                432, 431, 431, 430, 430, 429, 429, 
#                                428, 428, 427, 427, 426, 426, 425, 
#                                425, 424, 424, 423, 423, 422, 422, 
#                                421, 421, 420, 420, 419, 419, 418, 
#                                418, 417, 417, 401, 401, 402, 402, 
#                                403, 403, 404, 404, 405, 405, 406, 
#                                406, 407, 407, 408, 408, 409, 409, 
#                                410, 410, 411, 411, 412, 412, 413, 
#                                413, 414, 414, 415, 415, 416, 416, 
#                                400, 400, 399, 399, 398, 398, 397, 
#                                397, 396, 396, 395, 395, 394, 394, 
#                                393, 393, 392, 392, 391, 391, 390, 
#                                390, 389, 389, 388, 388, 387, 387, 
#                                386, 386, 385, 385, 369, 369, 370, 
#                                370, 371, 371, 372, 372, 373, 373, 
#                                374, 374, 375, 375, 376, 376, 377, 
#                                377, 378, 378, 379, 379, 380, 380, 
#                                381, 381, 382, 382, 383, 383, 384, 
#                                384, 368, 368, 367, 367, 366, 366, 
#                                365, 365, 364, 364, 363, 363, 362, 
#                                362, 361, 361, 360, 360, 359, 359, 
#                                358, 358, 357, 357, 356, 356, 355, 
#                                355, 354, 354, 353, 353, 337, 337, 
#                                338, 338, 339, 339, 340, 340, 341, 
#                                341, 342, 342, 343, 343, 344, 344, 
#                                345, 345, 346, 346, 347, 347, 348, 
#                                348, 349, 349, 350, 350, 351, 351, 
#                                352, 352, 336, 336, 335, 335, 334, 
#                                334, 333, 333, 332, 332, 331, 331, 
#                                330, 330, 329, 329, 328, 328, 327, 
#                                327, 326, 326, 325, 325, 324, 324, 
#                                323, 323, 322, 322, 321, 321, 305, 
#                                305, 306, 306, 307, 307, 308, 308, 
#                                309, 309, 310, 310, 311, 311, 312, 
#                                312, 313, 313, 314, 314, 315, 315, 
#                                316, 316, 317, 317, 318, 318, 319, 
#                                319, 320, 320, 304, 304, 303, 303, 
#                                302, 302, 301, 301, 300, 300, 299, 
#                                299, 298, 298, 297, 297, 296, 296, 
#                                295, 295, 294, 294, 293, 293, 292, 
#                                292, 291, 291, 290, 290, 289, 289, 
#                                273, 273, 274, 274, 275, 275, 276, 
#                                276, 277, 277, 278, 278, 279, 279, 
#                                280, 280, 281, 281, 282, 282, 283, 
#                                283, 284, 284, 285, 285, 286, 286, 
#                                287, 287, 288, 288, 272, 272, 271, 
#                                271, 270, 270, 269, 269, 268, 268, 
#                                267, 267, 266, 266, 265, 265, 264, 
#                                264, 263, 263, 262, 262, 261, 261, 
#                                260, 260, 259, 259, 258, 258, 257, 
#                                257, 241, 241, 242, 242, 243, 243, 
#                                244, 244, 245, 245, 246, 246, 247, 
#                                247, 248, 248, 249, 249, 250, 250, 
#                                251, 251, 252, 252, 253, 253, 254, 
#                                254, 255, 255, 256, 256, 240, 240, 
#                                239, 239, 238, 238, 237, 237, 236, 
#                                236, 235, 235, 234, 234, 233, 233, 
#                                232, 232, 231, 231, 230, 230, 229, 
#                                229, 228, 228, 227, 227, 226, 226, 
#                                225, 225, 209, 209, 210, 210, 211, 
#                                211, 212, 212, 213, 213, 214, 214, 
#                                215, 215, 216, 216, 217, 217, 218, 
#                                218, 219, 219, 220, 220, 221, 221, 
#                                222, 222, 223, 223, 224, 224, 208, 
#                                208, 207, 207, 206, 206, 205, 205, 
#                                204, 204, 203, 203, 202, 202, 201, 
#                                201, 200, 200, 199, 199, 198, 198, 
#                                197, 197, 196, 196, 195, 195, 194, 
#                                194, 193, 193, 177, 177, 178, 178, 
#                                179, 179, 180, 180, 181, 181, 182, 
#                                182, 183, 183, 184, 184, 185, 185, 
#                                186, 186, 187, 187, 188, 188, 189, 
#                                189, 190, 190, 191, 191, 192, 192, 
#                                176, 176, 175, 175, 174, 174, 173, 
#                                173, 172, 172, 171, 171, 170, 170, 
#                                169, 169, 168, 168, 167, 167, 166, 
#                                166, 165, 165, 164, 164, 163, 163, 
#                                162, 162, 161, 161, 145, 145, 146, 
#                                146, 147, 147, 148, 148, 149, 149, 
#                                150, 150, 151, 151, 152, 152, 153, 
#                                153, 154, 154, 155, 155, 156, 156, 
#                                157, 157, 158, 158, 159, 159, 160, 
#                                160, 144, 144, 143, 143, 142, 142, 
#                                141, 141, 140, 140, 139, 139, 138, 
#                                138, 137, 137, 136, 136, 135, 135, 
#                                134, 134, 133, 133, 132, 132, 131, 
#                                131, 130, 130, 129, 129, 113, 113, 
#                                114, 114, 115, 115, 116, 116, 117, 
#                                117, 118, 118, 119, 119, 120, 120, 
#                                121, 121, 122, 122, 123, 123, 124, 
#                                124, 125, 125, 126, 126, 127, 127, 
#                                128, 128, 112, 112, 111, 111, 110, 
#                                110, 109, 109, 108, 108, 107, 107, 
#                                106, 106, 105, 105, 104, 104, 103, 
#                                103, 102, 102, 101, 101, 100, 100, 
#                                99, 99, 98, 98, 97, 97, 81, 
#                                81, 82, 82, 83, 83, 84, 84, 
#                                85, 85, 86, 86, 87, 87, 88, 
#                                88, 89, 89, 90, 90, 91, 91, 
#                                92, 92, 93, 93, 94, 94, 95, 
#                                95, 96, 96, 80, 80, 79, 79, 
#                                78, 78, 77, 77, 76, 76, 75, 
#                                75, 74, 74, 73, 73, 72, 72, 
#                                71, 71, 70, 70, 69, 69, 68, 
#                                68, 67, 67, 66, 66, 65, 65, 
#                                49, 49, 50, 50, 51, 51, 52, 
#                                52, 53, 53, 54, 54, 55, 55, 
#                                56, 56, 57, 57, 58, 58, 59, 
#                                59, 60, 60, 61, 61, 62, 62, 
#                                63, 63, 64, 64, 48, 48, 47, 
#                                47, 46, 46, 45, 45, 44, 44, 
#                                43, 43, 42, 42, 41, 41, 40, 
#                                40, 39, 39, 38, 38, 37, 37, 
#                                36, 36, 35, 35, 34, 34, 33, 
#                                33, 17, 17, 18, 18, 19, 19, 
#                                20, 20, 21, 21, 22, 22, 23, 
#                                23, 24, 24, 25, 25, 26, 26, 
#                                27, 27, 28, 28, 29, 29, 30, 
#                                30, 31, 31, 32, 32, 16, 16, 
#                                15, 15, 14, 14, 13, 13, 12, 
#                                12, 11, 11, 10, 10, 9, 9, 
#                                8, 8, 7, 7, 6, 6, 5, 
#                                5, 4, 4, 3, 3, 2, 2, 
#                                1, 1]
 
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


    def readSlowControlFileintoFormattedList(self, filename):
        ''' Read the entire slow control file contents into a formatted list where each index 
            represents a word whose length corresponds to the width of that field: 
            i.e. MuxControl = 3 bits, Pixel Test and Feedback Control = 1 or 3 bits, BiasControl = 5 bits, etc
        '''
        slow_ctrl_file = open(filename, 'r')
        lines = slow_ctrl_file.readlines()
        slow_ctrl_file.close()    
        
        # List where each index is a five index list;
        #    Used to save serial control data from five column file structure
        data = []
        for line in lines:
            # Create a list of values contained in 'lines'
            ivals = [int(val) for val in split(strip(line))]
            # Append ivals list to data list
            data.append(ivals)

        slow_ctrl_length = len(data)
        
        # Variables used to construct variable length words from slow control data
        data_word = 0
        current_bit = 0
        # List for saving slow control words
        slow_ctrl_data = []

        # Process all 3904 bits
        for i in range(slow_ctrl_length):
            # Only process if Slow Control Enable(d) [ second column ]
            if data[i][1] == 1:
                
                # Mux Control
                if 0 <= i <= 1535:
                    # Save current bit
                    current_bit = data[i][2]
                    # Bit shift data_word before adding current_bit
                    data_word = data_word << 1
                    # Append current_bit to current data_word
                    data_word += current_bit
                    # Msb in five bit word between 3585-3589 is located at 3585
                    #    because 3585 % 5 = 0, check when % 5 = 4 to find lsb
                    if (i % 3) == 2:
                        slow_ctrl_data.append(data_word)
                        data_word = 0
                        
                # Pixel Self Test and Feedback Control
                elif 1536 <= i <= 3583:
                    # within each four bit word:
                    #    bit 0 = feedback select for pixel X, bit 1-3 = self test decoder for pixel X
                    bit_position = i % 4
                    if bit_position == 0:
                        # Feedback select for pixel X:
                        slow_ctrl_data.append( data[i][2] )
                        
                    else:
                        # Self test decoder for pixel X:
                        
                        # Save current bit
                        current_bit = data[i][2]
                        # Bit shift data_word before adding current_bit
                        data_word = data_word << 1
                        # Append current_bit to current data_word
                        data_word += current_bit
                        # Msb in five bit word between 3585-3589 is located at 3585
                        #    because 3585 % 5 = 0, check when % 5 = 4 to find lsb
                        if bit_position == 3:
                            slow_ctrl_data.append(data_word)
                            data_word = 0
                            
                # Self Test Enable
                elif i == 3584:
                    slow_ctrl_data.append( data[i][2] )

                # Bias Control
                elif 3585 <= i <= 3819:

                    # Save current bit
                    current_bit = data[i][2]
                    # Bit shift data_word before adding current_bit
                    data_word = data_word << 1
                    # Append current_bit to current data_word
                    data_word += current_bit
                    # Msb in five bit word between 3585-3589 is located at 3585
                    #    because 3585 % 5 = 0, check when % 5 = 4 to find lsb
                    if (i % 5) == 4:
                        slow_ctrl_data.append(data_word)
                        data_word = 0
                        
                # Spare Bits
                elif 3820 <= i <= 3824:
                    # Save current bit
                    current_bit = data[i][2]
                    # Bit shift data_word before adding current_bit
                    data_word = data_word << 1
                    # Append current_bit to current data_word
                    data_word += current_bit
                    # Lsb in 5 bit word between 3820-3824 is located at 3824
                    #    because 3824 % 5 = 4, that's the condition to find lsb and save that 5 bit word
                    if (i % 5) == 4:
                        slow_ctrl_data.append(data_word)
                        data_word = 0
                        
                # 100x Filter Control
                elif 3825 <= i <= 3844:
                    # Save current bit
                    current_bit = data[i][2]
                    # Bit shift data_word before adding current_bit
                    data_word = data_word << 1
                    # Append current_bit to current data_word
                    data_word += current_bit
                    # The first 19 bits are reserved (unused), it's only the lsb bit that is Filter Enable
                    if i == 3844:
                        slow_ctrl_data.append(data_word)
                        data_word = 0

                # ADC Delay Adjust
                elif 3845 <= i <= 3864:
                    # Save current bit
                    current_bit = data[i][2]
                    # Bit shift data_word before adding current_bit
                    data_word = data_word << 1
                    # Append current_bit to current data_word
                    data_word += current_bit
                    # The first 17 bits are reserved (unused), it's only the 3 lsb bits that is ADC Delay Adjust
                    if i == 3864:
                        slow_ctrl_data.append(data_word)
                        data_word = 0
                        
                # Digital Control
                elif 3865 <= i <= 3904:

                    if i < 3869:
                        # Reserved
                        # Save current bit
                        current_bit = data[i][2]
                        # Bit shift data_word before adding current_bit
                        data_word = data_word << 1
                        # Append current_bit to current data_word
                        data_word += current_bit
                        # Lsb in 7 bit word between 3865-3868 is located at 3868
                        #    because 3868 % 4 = 0, that's the condition to find lsb and save that 4 bit word
                        if (i % 4) == 0:
                            slow_ctrl_data.append(data_word)
                            data_word = 0

                    elif i < 3876:
                        # Reset 3 (gain stage 2)
                        # Save current bit
                        current_bit = data[i][2]
                        # Bit shift data_word before adding current_bit
                        data_word = data_word << 1
                        # Append current_bit to current data_word
                        data_word += current_bit
                        # Lsb in 7 bit word between 3869-3875 is located at 3875
                        #    because 3875 % 7 = 4, that's the condition to find lsb and save that 7 bit word
                        if (i % 7) == 4:
                            slow_ctrl_data.append(data_word)
                            data_word = 0

                    elif i < 3883:
                        # Reset 2 (gain stage 1)
                        current_bit = data[i][2]
                        # Bit shift data_word before adding current_bit
                        data_word = data_word << 1
                        # Append current_bit to current data_word
                        data_word += current_bit
                        # Lsb in 7 bit word between 3876-3882 is located at 3882
                        #    because 3882 % 7 = 4, that's the condition to find lsb and save that 7 bit word
                        if (i % 7) == 4:
                            slow_ctrl_data.append(data_word)
                            data_word = 0
                        
                    elif i < 3890:
                        # Reset 1 (pre-amp)
                        current_bit = data[i][2]
                        # Bit shift data_word before adding current_bit
                        data_word = data_word << 1
                        # Append current_bit to current data_word
                        data_word += current_bit
                        # Lsb in 7 bit word between 3883-3889 is located at 3889
                        #    because 3889 % 7 = 4, that's the condition to find lsb and save that 7 bit word
                        if (i % 7) == 4:
                            slow_ctrl_data.append(data_word)
                            data_word = 0

                    elif i < 3897:
                        # Clock counter offset
                        current_bit = data[i][2]
                        # Bit shift data_word before adding current_bit
                        data_word = data_word << 1
                        # Append current_bit to current data_word
                        data_word += current_bit
                        # Lsb in 7 bit word between 3890-3897 is located at 3897
                        #    because 3897 % 7 = 4, that's the condition to find lsb and save that 7 bit word
                        if (i % 7) == 4:
                            slow_ctrl_data.append(data_word)
                            data_word = 0

                    else:
                        # Clock select
                        current_bit = data[i][2]
                        # Bit shift data_word before adding current_bit
                        data_word = data_word << 1
                        # Append current_bit to current data_word
                        data_word += current_bit
                        # Lsb in 7 bit word between 3904-3904 is located at 3904
                        #    because 3904 % 7 = 4, that's the condition to find lsb and save that 7 bit word
                        if (i % 7) == 4:
                            slow_ctrl_data.append(data_word)
                            data_word = 0
        
        return slow_ctrl_data, len(slow_ctrl_data)
    
    
    
    def readSlowControlFileIntoList(self, filename):
        ''' NO LONGER OF ANY USE
            Reads all the slow control file into a list containing 32 bit words '''
        slow_ctrl_file = open(filename, 'r')
        lines = slow_ctrl_file.readlines()
        slow_ctrl_file.close()    
        
        data = []
        for line in lines:
            # Create a list of values contained in lines
            ivals = [int(val) for val in split(strip(line))]
            # Append ivals list to data list
            data.append(ivals)
            
        i_max = len(data)
        
        no_words = i_max
        if i_max%32:
            no_words = no_words + 1
            
        slow_ctrl_data = [0l] * no_words
    
        lsb = 0
        k = 0
        nbits = 0
        data_word = 0l
        current_bit = 0

        print "readSlowControl.. Function, number of words: ", no_words

#        print "before: curr_bit, data_word / Mid: data_word / After: curr_bit, data_word:"
        
        # Process all 3904 bits
        for i in range(i_max):
                # Save current bit
                current_bit = data[i][2]

                # Bit shift data_word before adding current_bit
                data_word = data_word << 1
                
                # Append current_bit to current data_word
                data_word += current_bit
                
                # Msb in five bit word between 3585-3589 is located at 3585
                #    because 3585 % 5 = 0, check when % 5 = 4 to find lsb
                if (i % 32) == 31:
                    slow_ctrl_data[k] = data_word
                    data_word = 0
                    k = k +1


                
        return slow_ctrl_data, k
        
    def convertListIntoXmlFile(self, scList):
        """ Convert the formatted scList into an xml file """

        filename = ExtractSlowControlParamsFromFile.currentDir + '/SlowControlMachined.xml'
        try:
            xml_file = open(filename, 'w')
        except Exception as e:
            print "convertListIntoXmlFile: Couldn't open file: ", e

        stringList = []
        # XML header information
        stringList.append( '''<?xml version="1.0"?>''')
        stringList.append( '''   <lpd_slow_ctrl_sequence name="SlowControlMachined.xml"''')
        stringList.append( '''   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"''')
        stringList.append( '''   xsi:noNamespaceSchemaLocation="lpdSlowCtrlSequence.xsd">''')
        stringList.append( '''   <!-- This file is script generated by ExtractSlowControlParamsFromFile.py -->''')
        
        # Check whether all of Mux Control values are zero; if all zero, use mux_decoder_pixel_default instead of 512 zero'd XML tags
        # Assume all 512 values are zero
        bMuxControlAllZero = True
        # To same check on feedback_select and self_test_decoder
        bFeedbackSelectAllZero = True
        bSelfTestDecoderAllZero = True
        
        # Loop over all mux_decoder values..
        for i in range(512):
            # Is this decoder nonzero?
            if scList[i] > 0:
                print "Yes?"
                bMuxControlAllZero = False
                
        # Loop over all feedback_select values..
        for i in range(512, 1536, 2):
            # Is this feedback_select nonzero?
            if scList[i] > 0:
                bFeedbackSelectAllZero = False

        # Loop over all self_test_decoder values..
        for i in range(513, 1536, 2):
            # Is this self_test_decoder nonzero?
            if scList[i] > 0:
                bSelfTestDecoderAllZero = False

                
        # Mux Control configuration: If only zero value detected..
        if bMuxControlAllZero:
            # ..Only populate Master
            stringList.append( '''   <mux_decoder_default value="0"/>''' )
        else:
            # ..else populate all 512 keys
            for idx in range(512):
                stringList.append( '''   <mux_decoder pixel="%i"''' % (ExtractSlowControlParamsFromFile.muxDecoderLookupTable[idx]- 1) +''' value="%i"/>''' % scList[0+idx] )


        # Pixel Self Test and Feedback Control configuration
        
        # Are all feedback_select keys 0?
        if bFeedbackSelectAllZero:
            # All Zeros; use _default tag
            stringList.append( '''   <feedback_select_default value="0"/>''')
        else:
            for idx in range(512):
                # feedback select (pixel = idx)
                stringList.append( '''   <feedback_select pixel="%i"''' % (ExtractSlowControlParamsFromFile.pixelSelfTestLookupTable[idx*2]- 1) +''' value="%i"/>''' % scList[512+(idx*2)] )

        # Are all self_test_decoder keys 0?
        if bSelfTestDecoderAllZero:
            # All Zero; you _default tag
            stringList.append( '''   <self_test_decoder_default value="0"/>''')
        else:        
            for idx in range(512):
                # pixel self test (pixel = idx)
                stringList.append( '''   <self_test_decoder pixel="%i"''' % (ExtractSlowControlParamsFromFile.pixelSelfTestLookupTable[(idx*2) +1]- 1) +''' value="%i"/>''' % scList[512+(idx*2)+1] )
                # Note that each pixel is listed twice in the list, ie [0, 0, 1, 1, 2, 2, .., Etc]
        
        # Self Test Enable
        stringList.append( '''   <self_test_enable value="%i"/>''' % scList[1536] )
        
        # Bias Control configuration
        for idx in range(47):
            stringList.append( '''   <daq_bias index="%i"''' % (ExtractSlowControlParamsFromFile.biasCtrlLookupTable[idx]- 1) +''' value="%i"/>''' % scList[1537+idx] )
        
        # Spare bits
        stringList.append( '''   <spare_bits value="%i"/>''' % scList[1584] )
        
        
        # Write XML Tags to file
        for i in range(len(stringList)):
            xml_file.write( stringList[i] +'\n')

        # Write closing tag to file
        xml_file.write('''</lpd_slow_ctrl_sequence> ''' +'\n')
        
        try:
            xml_file.close()
        except Exception as e:
            print "convertListIntoXmlFile: Couldn't close file: ", e
            
        if xml_file.closed:
            pass
        else:
            print "File still opened."

    def displayFormattedList(self, scList, list_length):
        """ display section by section the values already extracted from slow control configuration file (not an XML file!) """
        
        print "list_length ", list_length
        print "actual length ", len(scList)
        print "scList:"
        print "MuxControl: \t",     scList[0:512]
        print "PxlSelfTest:\t",     scList[512:1536]
        print "SelfTest:\t",        scList[1536:1537]
        print "BiasControl:\t",     scList[1537:1584]
        print "SpareBits:\t",       scList[1584:1585]
        print "100xFilter:\t",      scList[1585:1586]
        print "ADCclockDelay:\t",   scList[1586:1587]
        print "DigitalCtrl:\t",     scList[1587:1593]
        
    def createMuxDecoderDictKeysAndLookupTable(self):
        """ this function is used to produce the lookup table required for the mux_decoder_pixel_XX tags
            there are 512 of these (not counting the master one) and this function is only likely to be run 1-2 times at most
        """
        
        # Create number in order for mux decoder pixels
        numberList = []
        for row in range(32):
            for col in range(512-row, 0,-32):
                numberList.append(col)

        pixels = 512

        """ create the lookup table for Mux Decoder settings that will be used inside this script """

        filename = ExtractSlowControlParamsFromFile.currentDir + '/scMuxLookupTable.txt'
        try:
            lookup_file = open(filename, 'w')
        except Exception as e:
            print "createMuxDecoderDictKeysAndLookupTable: Couldn't open 2nd file because: ", e
        
        # Preamble..
        lookup_file.write("muxDecoderLookupTable = [")
        
        ''' Extract 'mux_decoder_pixel_' section from each key name.. '''
        for idx in range(pixels): 
            # Write value to file
            lookup_file.write( "%3i, " % numberList[idx] )
            # Limit table to 16 entries per row
            if ((idx % 16) == 15):
                lookup_file.write("\n\t\t\t")
        # Close list with ] 
        lookup_file.write("]")    
        
        # The list should similar to this:
        '''[512, 480, 448, 416, ...]'''
        
        try:
            lookup_file.close()
        except Exception as e:
            print "createMuxDecoderDictKeysAndLookupTable: Couldn't close 2nd file because: ", e
        
    def createPixelSelfTestAndFeedbackControlDictKeysAndLookupTable(self):
        """ 
            DUFF !
            Function to be used once or twice for creating the dictionary keys and lookup table 
        """

        ''' The old implementation which created an incorrect lookup table '''
        pass
#        old_start = 497
#        new_start = 497
#        # Pixel numbering from 1-512 is represented in Python by 0-511.
#        #    So in order to number from 1-512 in Python, we must run until 513
#        old_stop = 513
#        new_stop = 513
#        # Direction, positive = incremental, negative = decremental
#        dir = 1
#        pxlList = []
#        for i in range(32):
#            # Save start and stop values from previous iteration
#            old_start = new_start
#            old_stop = new_stop
#            for i in range(new_start, new_stop, dir):
#                pxlList.append(i)
#            # Calculate next iteration's start and stop that is based upon the previous.
#            #    Note that the distance fluctuates between either 17 or 15 from one row to the next
#        
#            new_start = old_stop-16-dir
#            new_stop = old_start-16-dir
#            dir = dir * (-1)
#
#        # Create dictionary lookup table  
#        lookupTableList = []
#        pixelTestFeedback_offset = 0x00 # This will be 1 for feedback and 3 for self test
#        pixels = 512
#        
#        # Generate dictionary keys to be used inside LpdSlowCtrlSequence.py
#        for idx in range(pixels):
#            pixelTestFeedback_offset += 1
#            lookupTableList.append( """                         'feedback_select_pixel_%i'""" % pxlList[idx] + """    : pixelSelfTest + 0x%03x,\n""" % (pixelTestFeedback_offset) )
#            pixelTestFeedback_offset += 3
#            lookupTableList.append( """                         'self_test_pixel_%i'""" % pxlList[idx] + """          : pixelSelfTest + 0x%03x,\n""" % (pixelTestFeedback_offset) )
#
#        # Write dictionary keys and values to file
#        filename = ExtractSlowControlParamsFromFile.currentDir + '/scSelfTestDictKeys.txt'
#        try:
#            pixeltest_file = open(filename, 'w')
#        except Exception as e:
#            print "createPixelSelfTestAndFeedbackControlDictKeysAndLookupTable: Couldn't open file because: ", e
#        
#        # Write these dictionary keys to file; Note each pixel has two settings, ie 1024 or 512*2
#        for idx in range(pixels*2):
#            pixeltest_file.write( lookupTableList[idx] )
#        
#        try:
#            pixeltest_file.close()
#        except Exception as e:
#            print "createPixelSelfTestAndFeedbackControlDictKeysAndLookupTable: Couldn't close file because: ", e
#         
#
#        """ create the lookup table for Mux Decoder settings that will be used inside this script """
#
#        filename = ExtractSlowControlParamsFromFile.currentDir + '/scSelfTestLookupTable.txt'
#        try:
#            lookup_file = open(filename, 'w')
#        except Exception as e:
#            print "createPixelSelfTestAndFeedbackControlDictKeysAndLookupTable: Couldn't open 2nd file because: ", e
#        
#        # Preamble..
#        lookup_file.write("pixelSelfTestLookupTable = [")
#        
#        ''' Extract 'feedback_select_pixel_' /'self_test_pixel_' section from each key name.. '''
#        for idx in range(pixels*2):    
#            # Remove leading whitespaces
#            noPreSpaces = lookupTableList[idx].strip()
#            # Select key name
#            keyName = noPreSpaces[0:26]
#            # Remove apostrophies
#            noApos = keyName.replace("'", "")
#            # Remove remaining whitespaces
#            noSpaces = noApos.replace(" ", "")
#            # Write keyname to file
#            lookup_file.write( "\"" + noSpaces + "\", ")
#            
#            if idx % 7 == 6:
#                lookup_file.write("\n")
#
#        # Close list with ] ..
#        lookup_file.write("]")    
#        
#        # The list should similar to this:
#        '''["feedback_select_pixel_497", "self_test_pixel_497", "feedback_select_pixel_498", ...'''
#        
#        try:
#            lookup_file.close()
#        except Exception as e:
#            print "createPixelSelfTestAndFeedbackControlDictKeysAndLookupTable: Couldn't close 2nd file because: ", e

    def new__createPixelSelfTestAndFeedbackLookupTable(self):
        """ Function to be used once for creating feedback_select/self_test_decoder lookup table """
        
        old_start = 497
        new_start = 497
        # Pixel numbering from 1-512 is represented in Python by 0-511.
        #    So in order to number from 1-512 in Python, we must run until 513
        old_stop = 513
        new_stop = 513
        # Direction, positive = incremental, negative = decremental
        dir = 1
        pxlList = [0] * 512
        counter = 0
        for i in range(32):
            # Save start and stop values from previous iteration
            old_start = new_start
            old_stop = new_stop
            for i in range(new_start, new_stop, dir):
                pxlList[i-1] = counter
                counter += 1

            # Calculate next iteration's start and stop that is based upon the previous.
            #    Note that the distance fluctuates between either 17 or 15 from one row to the next
            new_start = old_stop-16-dir
            new_stop = old_start-16-dir
            dir = dir * (-1)

        pixels = 512
        
        """ create the lookup table for Pixel Self Test and Feedback settings that will be used inside this script """

        filename = ExtractSlowControlParamsFromFile.currentDir + '/scSelfTestLookupTable.txt'
        try:
            lookup_file = open(filename, 'w')
        except Exception as e:
            print "__new__...():  Couldn't open 2nd file because: ", e
        
        # Preamble..
        lookup_file.write("pixelSelfTestLookupTable = [")
        
        for idx in range(pixels):
            # Write value to file
            lookup_file.write( "%3i, " % pxlList[idx] )
            # Limit table to 16 entries per row
            if ((idx % 16) == 15):
                lookup_file.write("\n\t\t\t")

        # Close list with ] ..
        lookup_file.write("]")    
        
        # The list should similar to this:
        '''[511, 510, 509, .., 496, 480, 481, .., 495, 479, 478, ...'''
        
        try:
            lookup_file.close()
        except Exception as e:
            print "__new__...():  Couldn't close 2nd file because: ", e

    def createBiasControlDictKeysAndLookupTable(self):
        """ this function produces the lookup table required for the daq_bias tags
            there are 512 these (not counting the master one) and this function is only likely to be run 1-2 times at most
        """

        # Create number in order for daq_bias 
        numberList = [47, 46, 21, 15, 9, 36, 45, 19, 14, 8, 44, 32, 18, 12, 5, 43, 30, 17, 11, 2, 42, 24, 16, 10, 1, 
                      41, 37, 28, 23, 7, 35, 33, 27, 22, 6, 40, 31, 26, 20, 4, 39, 29, 25, 13, 3, 38, 34]
                
        counter = 0
        lookupTableList = [0] * 47
        # Generate corrected lookup table
        for idx in range(len(numberList)):
            lookupTableList[ numberList[idx]- 1 ] = counter
            counter += 1

    
        """ create the lookup table for bias Decoder settings that will be used inside this script """

        filename = ExtractSlowControlParamsFromFile.currentDir + '/scBiasLookupTable.txt'
        try:
            lookup_file = open(filename, 'w')
        except Exception as e:
            print "createBiasControlDictKeysAndLookupTable: Couldn't open 2nd file because: ", e
        
        # Preamble..
        lookup_file.write("biasDecoderLookupTable = [")
        
        # Write lookup table to file
        for idx in range( len(numberList)):
            # Write value to file
            lookup_file.write( "%3i, " % lookupTableList[idx] )
            # Limit table to 16 entries per row
            if ((idx % 16) == 15):
                lookup_file.write("\n\t\t\t")

        # Close list with ] ..
        lookup_file.write("]")
        
        try:
            lookup_file.close()
        except Exception as e:
            print "createBiasControlDictKeysAndLookupTable: Couldn't close 2nd file because: ", e


if __name__ == "__main__":
    
    thisFile = ExtractSlowControlParamsFromFile.currentDir

    slowControlParams = ExtractSlowControlParamsFromFile()
    slow_ctrl_data, list_length = slowControlParams.readSlowControlFileintoFormattedList( thisFile + '/SlowCtrlCmds.txt')
    
    # Display section by section the slow control values extracted from the file above
#    slowControlParams.displayFormattedList(slow_ctrl_data, list_length)


    ''' Create dictionary keys and the lookup table required for mux_decoder_pixel_xxx (used by LpdSlowCtrlSequence.py and this script)
        DONE ''' 
    slowControlParams.createMuxDecoderDictKeysAndLookupTable()
    print "mux table generated."
    
    ''' Create a unified lookup table for feedback_select/self_test_decoder '''
    ''' Create dictionary keys / lookup table required for Pixel Self Test and Feedback Control '''
    print "testing the new__createPixelSelfTestAndFeedbackLookupTable() function.."
    slowControlParams.new__createPixelSelfTestAndFeedbackLookupTable()
    
    print "Generating at the corrected daq bias lookup table"
    slowControlParams.createBiasControlDictKeysAndLookupTable()
    
    ''' Convert these into an XML file - Should handle the lot '''
    
    print "Calling convertListIntoXmlFile().."
    slowControlParams.convertListIntoXmlFile(slow_ctrl_data)
    print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
        