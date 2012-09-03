'''
Created on Aug 29, 2012

@author: ckd27546
'''

# Import Python standard modules
from string import strip, split
#import time

class ExtractSlowControlParamsFromFile():

    # Lookup tables for the various sections of the slow control configuration file
    biasCtrlLookupTable = ["daq_bias_47", "daq_bias_46", "daq_bias_21", "daq_bias_15", "daq_bias_9", "daq_bias_36", "daq_bias_45", "daq_bias_19", "daq_bias_14", "daq_bias_8", "daq_bias_44", 
                        "daq_bias_32", "daq_bias_18", "daq_bias_12", "daq_bias_5", "daq_bias_43", "daq_bias_30", "daq_bias_17", "daq_bias_11", "daq_bias_2", "daq_bias_42", "daq_bias_24", 
                        "daq_bias_16", "daq_bias_10", "daq_bias_1", "daq_bias_41", "daq_bias_37", "daq_bias_28", "daq_bias_23", "daq_bias_7", "daq_bias_35", "daq_bias_33", "daq_bias_27", 
                        "daq_bias_22", "daq_bias_6", "daq_bias_40", "daq_bias_31", "daq_bias_26", "daq_bias_20", "daq_bias_4", "daq_bias_39", "daq_bias_29", "daq_bias_25", "daq_bias_13", 
                        "daq_bias_3", "daq_bias_38", "daq_bias_34"]

    def readSlowControlFileintoFormattedList(self, filename):
        ''' Read the entire slow control file contents into a formatted list where each index 
            represents a word whose length corresponds to the width of that field: 
            i.e. MuxControl = 3 bits, Pixel Test and Feedback Control = 1 or 3 bits, BiasControl = 5 bits, etc
        '''
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
            
        slow_ctrl_data = [0] * no_words
    
        lsb = 0
        k = 0
        nbits = 0
        data_word = 0
        current_bit = 0

#        print data[3585:3585+16]

        # Process all 3904 bits
        for i in range(i_max):
            # Only process if Slow Control Enable(d) [ second column ]
            if data[i][1] == 1:
                nbits = nbits + 1
                
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
                        slow_ctrl_data[k] = data_word
                        data_word = 0
                        k = k +1
                        
                # Pixel Self Test and Feedback Control
                elif 1536 <= i <= 3583:
                    # within each four bit word:
                    #    bit 0 = feedback select for pixel X, bit 1-3 = self test decoder for pixel X
                    bit_position = i % 4
                    if bit_position == 0:
                        # Feedback select for pixel X:
                        slow_ctrl_data[k] = data[i][2]
                        k = k +1
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
                            slow_ctrl_data[k] = data_word
                            data_word = 0
                            k = k +1
                            
                # Self Test Enable
                elif i == 3584:
                    slow_ctrl_data[k] = data[i][2]
                    k = k +1
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
                        slow_ctrl_data[k] = data_word
                        data_word = 0
                        k = k +1
                # Spare Bits
                elif 3820 <= i <= 3824:
                    if i <= 3821:
                        # Spare bits: no current use
                        pass
                    elif i <= 3822:
                        # Gain Switching Mode
                        slow_ctrl_data[k] = data[i][2]
                        k = k +1
                    elif i <= 3823:
                        # Calibration Pad Vcalib Buff input switch
                        slow_ctrl_data[k] = data[i][2]
                        k = k +1
                    else:# i <= 3824:
                        # Adc Alternative Pad Input Switch
                        slow_ctrl_data[k] = data[i][2]
                        k = k +1
                # 100x Filter Control
                elif 3825 <= i <= 3844:
                    if i < 3844:
                        # 19 unused bits
                        pass
                    else:
                        # Filter Enable
                        slow_ctrl_data[k] = data[i][2]
                        k = k +1

                # ADC Delay Adjust
                elif 3845 <= i <= 3864:
                    if i < 3862:
                        # 17 unused bits
                        pass
                    else:
                        # Delay Adjust
                        # Save current bit
                        current_bit = data[i][2]
                        # Bit shift data_word before adding current_bit
                        data_word = data_word << 1
                        # Append current_bit to current data_word
                        data_word += current_bit
                        # Lsb in 3 bit word between 3862-3864 is located at 3864
                        #    because 3864 % 3 = 0, that's the condition to find lsb and save that 3 bit word
                        if (i % 3) == 0:
                            slow_ctrl_data[k] = data_word
                            data_word = 0
                            k = k +1
                # Digital Control
                elif 3865 <= i <= 3904:
                    if i < 3869:
                        # Reserved
                        pass
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
                            slow_ctrl_data[k] = data_word
                            data_word = 0
                            k = k +1

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
                            slow_ctrl_data[k] = data_word
                            data_word = 0
                            k = k +1
                        
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
                            slow_ctrl_data[k] = data_word
                            data_word = 0
                            k = k +1

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
                            slow_ctrl_data[k] = data_word
                            data_word = 0
                            k = k +1

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
                            slow_ctrl_data[k] = data_word
                            data_word = 0
                            k = k +1

                
        return slow_ctrl_data, k
    
    
    
    def readSlowControlFileIntoList(self, filename):
        ''' Reads all the slow control file into a list containing 32 bit words '''
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
                
#                '''test'''
#                if k == 112:
#                    print "a: ", current_bit, data_word,

#                if 3585 <= i <= 3594:#3589:
#                    if i % 5 ==0:
#                        print "k = ", k
#                    print "@i: ", i, " found: ", current_bit

                # Bit shift data_word before adding current_bit
                data_word = data_word << 1
                
#                if k == 112:
#                    print " b: ", data_word,
                # Append current_bit to current data_word
                data_word += current_bit

#                if k == 112:
#                    print "\t c: ", current_bit, data_word

                
                # Msb in five bit word between 3585-3589 is located at 3585
                #    because 3585 % 5 = 0, check when % 5 = 4 to find lsb
                if (i % 32) == 31:
                    slow_ctrl_data[k] = data_word
                    data_word = 0
                    k = k +1


                
        return slow_ctrl_data, k
    
    def convertListInto32BitWord(self, scList):
        """ Accepts a list of slow control words (where each index represents a word of one or several bits)
            and convert this into the format that is currently accepted by the firmware; i.e., each word consists of 32 bits """
        
        #TODO: expand function to cover all the different types of slow control parameters, not just the Bias Control.
        
        
        thirtytwoBitWord = 0l
        lsbs = 0
        # Combine the first seven words to create the first 32 bit word
        for i in range(7):
            # Special case if current word straddles a 32 bit boundary
            if i % 7 == 6:
                # Only want to most significant bits
                lsbs = scList[i] & 24
                # Bit shift these 2 msb to lsb position
                print "lsbs: ", lsbs,
                lsbs = lsbs >> 3
                print lsbs
                thirtytwoBitWord += lsbs
            else:
#                print (5-i),
                val = scList[i] << (5* (5-i) + 2)
                print "%X" % val
                thirtytwoBitWord += val
                
        print ""
        return thirtytwoBitWord
    
    def convertListIntoXmlFile(self, scList):
        """ Convert the formatted scList into an xml file """
        filename = '/u/ckd27546/lpd_workspace/workspace_temp/LpdCommandSequence/SlowControlMachined.xml'
        try:
            xml_file = open(filename, 'w')
        except Exception as errNo:
            print "convertListIntoXmlFile: Couldn't open file: ", errNo

        stringList = []
        # XML header information
        stringList.append( '''<?xml version="1.0"?>''')
        stringList.append( '''   <lpd_slow_ctrl_sequence name="SlowControlMachined.xml"''')
        stringList.append( '''   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"''')
        stringList.append( '''   xsi:noNamespaceSchemaLocation="lpdSlowCtrlSequence.xsd">''')
        stringList.append( '''   <!-- This file is script generated by ExtractSlowControlParamsFromFile.py >''')
        
        # Bias Control configuration
        for idx in range(47):
            stringList.append( '''   <%s''' % ExtractSlowControlParamsFromFile.biasCtrlLookupTable[idx] +''' count=%i>''' % scList[1537+idx] )
        
        # Write XML Tags to file
        for i in range(len(stringList)):
            xml_file.write( stringList[i] +'\n')

        # Write closing tag to file
        xml_file.write('''</lpd_slow_ctrl_sequence> ''' +'\n')
        
        try:
            xml_file.close()
        except Exception as errNo:
            print "convertListIntoXmlFile: Couldn't close file: ", errNo
            
        if xml_file.closed:
            print "File is closed." # The file is closed
        else:
            print "File still opened."

    def displayFormattedList(self, scList, list_length):
        """ display section by section the values already extracted from slow control configuration file (not the XML file) """
        
        print "list_length ", list_length
        print "scList:"
#        print "MuxControl: \t",     scList[0:512]
#        print "PxlSelfTest:\t",     scList[512:1536]
        print "SelfTest:\t",        scList[1536:1537]
        print "BiasControl:\t",     scList[1537:1584]
        print "SpareBits:\t",       scList[1584:1589]
        print "100xFilter:\t",      scList[1589:1609]
        print "ADCclockDelay:\t",   scList[1609:1629]
        print "DigitalCtrl:\t",     scList[1629:1669]
        
    def createMuxDecoderTable(self):
        """ this function is used to produce the lookup table required for the mux_decoder_pixel_XX tags
            there are 512 these (not counting the master one) and this function is only likely to be run 1-2 times at most
        """
        filename = '/u/ckd27546/lpd_workspace/workspace_temp/LpdCommandSequence/scMuxTable.txt'
        try:
            lookup_file = open(filename, 'w')
        except Exception as errNo:
            print "createMuxDecoderTable: Couldn't open file because: ", errNo
        
        # Create number in order for mux decoder pixels
        numberList = []
        for row in range(16):
            for col in range(512-row, 0,-16):
                numberList.append(col)
        
        lookupTableList = []
        mux_offset = 0x03
        pixels = 512
        
        for idx in range(pixels):
            lookupTableList.append( """                         'mux_decoder_pixel_%i'""" % numberList[idx] + """        : 0x0%x,\n""" % (mux_offset + idx*3) )
        
        # Each line should look similar to this:
        """                         'mux_decoder_pixel_512'        : 0x03,"""
        
        for idx in range(pixels):
            lookup_file.write( lookupTableList[idx] )
        
        try:
            lookup_file.close()
        except Exception as errNo:
            print "createdMuxDecoderTable: Couldn't close file because: ", errNo

        

if __name__ == "__main__":
    slowControlParams = ExtractSlowControlParamsFromFile()
    slow_ctrl_data, list_length = slowControlParams.readSlowControlFileintoFormattedList('/u/ckd27546/lpd_workspace/workspace_temp/LpdCommandSequence/SlowCtrlCmds.txt')
    
#    slowControlParams.displayFormattedList(slow_ctrl_data, list_length)
#
#    print "Calling convertListIntoXmlFile().."
#    slowControlParams.convertListIntoXmlFile(slow_ctrl_data)
#    print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

    # Creating the lookup table are required for mux_decoder_pixel_xxx tags..
    slowControlParams.createMuxDecoderTable()
    
    
    
    # Print the first 32-bit word contained in the Bias Control:
#    print "%X" % slowControlParams.convertListInto32BitWord(slow_ctrl_data)
    
    ''' Testing reading in entire file into a list of 32-bit words '''
#    slow_ctrl_data, list_length = slowControlParams.readSlowControlFileIntoList('/u/ckd27546/lpd_workspace/workspace_temp/LpdCommandSequence/SlowCtrlCmds.txt')
#    
#    print "Mux Control: \t\t\t\t", slow_ctrl_data[0:47]
#    print "Pixel Self Test and Feedback Control: ", slow_ctrl_data[48:111]
##    print "Self Test Enable: ", slow_ctrl_data[    # Self test is only one bit, ie the most significant bit in the first word of Bias Control:
#    print "Bias Control: \t\t", 
#    for i in range(112,120):
#        print "%X" % slow_ctrl_data[i], 
#    
#    print " (and a few of the bits from the next section..)"
#    print "Spare Bits: (..)"
#    
#    for i in range(110,list_length):
#        print "slow_ctrl_data[", i, "]: %X " % slow_ctrl_data[i]
#        