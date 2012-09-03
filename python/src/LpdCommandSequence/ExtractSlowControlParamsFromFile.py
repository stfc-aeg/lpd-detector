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
    muxDecoderLookupTable = ["mux_decoder_pixel_512", "mux_decoder_pixel_496", "mux_decoder_pixel_480", "mux_decoder_pixel_464", "mux_decoder_pixel_448", "mux_decoder_pixel_432", "mux_decoder_pixel_416", 
                             "mux_decoder_pixel_400", "mux_decoder_pixel_384", "mux_decoder_pixel_368", "mux_decoder_pixel_352", "mux_decoder_pixel_336", "mux_decoder_pixel_320", "mux_decoder_pixel_304", 
                             "mux_decoder_pixel_288", "mux_decoder_pixel_272", "mux_decoder_pixel_256", "mux_decoder_pixel_240", "mux_decoder_pixel_224", "mux_decoder_pixel_208", "mux_decoder_pixel_192", 
                             "mux_decoder_pixel_176", "mux_decoder_pixel_160", "mux_decoder_pixel_144", "mux_decoder_pixel_128", "mux_decoder_pixel_112", "mux_decoder_pixel_96", "mux_decoder_pixel_80", 
                             "mux_decoder_pixel_64", "mux_decoder_pixel_48", "mux_decoder_pixel_32", "mux_decoder_pixel_16", "mux_decoder_pixel_511", "mux_decoder_pixel_495", "mux_decoder_pixel_479", 
                             "mux_decoder_pixel_463", "mux_decoder_pixel_447", "mux_decoder_pixel_431", "mux_decoder_pixel_415", "mux_decoder_pixel_399", "mux_decoder_pixel_383", "mux_decoder_pixel_367", 
                             "mux_decoder_pixel_351", "mux_decoder_pixel_335", "mux_decoder_pixel_319", "mux_decoder_pixel_303", "mux_decoder_pixel_287", "mux_decoder_pixel_271", "mux_decoder_pixel_255", 
                             "mux_decoder_pixel_239", "mux_decoder_pixel_223", "mux_decoder_pixel_207", "mux_decoder_pixel_191", "mux_decoder_pixel_175", "mux_decoder_pixel_159", "mux_decoder_pixel_143", 
                             "mux_decoder_pixel_127", "mux_decoder_pixel_111", "mux_decoder_pixel_95", "mux_decoder_pixel_79", "mux_decoder_pixel_63", "mux_decoder_pixel_47", "mux_decoder_pixel_31", 
                             "mux_decoder_pixel_15", "mux_decoder_pixel_510", "mux_decoder_pixel_494", "mux_decoder_pixel_478", "mux_decoder_pixel_462", "mux_decoder_pixel_446", "mux_decoder_pixel_430", 
                             "mux_decoder_pixel_414", "mux_decoder_pixel_398", "mux_decoder_pixel_382", "mux_decoder_pixel_366", "mux_decoder_pixel_350", "mux_decoder_pixel_334", "mux_decoder_pixel_318", 
                             "mux_decoder_pixel_302", "mux_decoder_pixel_286", "mux_decoder_pixel_270", "mux_decoder_pixel_254", "mux_decoder_pixel_238", "mux_decoder_pixel_222", "mux_decoder_pixel_206", 
                             "mux_decoder_pixel_190", "mux_decoder_pixel_174", "mux_decoder_pixel_158", "mux_decoder_pixel_142", "mux_decoder_pixel_126", "mux_decoder_pixel_110", "mux_decoder_pixel_94", 
                             "mux_decoder_pixel_78", "mux_decoder_pixel_62", "mux_decoder_pixel_46", "mux_decoder_pixel_30", "mux_decoder_pixel_14", "mux_decoder_pixel_509", "mux_decoder_pixel_493", 
                             "mux_decoder_pixel_477", "mux_decoder_pixel_461", "mux_decoder_pixel_445", "mux_decoder_pixel_429", "mux_decoder_pixel_413", "mux_decoder_pixel_397", "mux_decoder_pixel_381", 
                             "mux_decoder_pixel_365", "mux_decoder_pixel_349", "mux_decoder_pixel_333", "mux_decoder_pixel_317", "mux_decoder_pixel_301", "mux_decoder_pixel_285", "mux_decoder_pixel_269", 
                             "mux_decoder_pixel_253", "mux_decoder_pixel_237", "mux_decoder_pixel_221", "mux_decoder_pixel_205", "mux_decoder_pixel_189", "mux_decoder_pixel_173", "mux_decoder_pixel_157", 
                             "mux_decoder_pixel_141", "mux_decoder_pixel_125", "mux_decoder_pixel_109", "mux_decoder_pixel_93", "mux_decoder_pixel_77", "mux_decoder_pixel_61", "mux_decoder_pixel_45", 
                             "mux_decoder_pixel_29", "mux_decoder_pixel_13", "mux_decoder_pixel_508", "mux_decoder_pixel_492", "mux_decoder_pixel_476", "mux_decoder_pixel_460", "mux_decoder_pixel_444", 
                             "mux_decoder_pixel_428", "mux_decoder_pixel_412", "mux_decoder_pixel_396", "mux_decoder_pixel_380", "mux_decoder_pixel_364", "mux_decoder_pixel_348", "mux_decoder_pixel_332", 
                             "mux_decoder_pixel_316", "mux_decoder_pixel_300", "mux_decoder_pixel_284", "mux_decoder_pixel_268", "mux_decoder_pixel_252", "mux_decoder_pixel_236", "mux_decoder_pixel_220", 
                             "mux_decoder_pixel_204", "mux_decoder_pixel_188", "mux_decoder_pixel_172", "mux_decoder_pixel_156", "mux_decoder_pixel_140", "mux_decoder_pixel_124", "mux_decoder_pixel_108", 
                             "mux_decoder_pixel_92", "mux_decoder_pixel_76", "mux_decoder_pixel_60", "mux_decoder_pixel_44", "mux_decoder_pixel_28", "mux_decoder_pixel_12", "mux_decoder_pixel_507", 
                             "mux_decoder_pixel_491", "mux_decoder_pixel_475", "mux_decoder_pixel_459", "mux_decoder_pixel_443", "mux_decoder_pixel_427", "mux_decoder_pixel_411", "mux_decoder_pixel_395", 
                             "mux_decoder_pixel_379", "mux_decoder_pixel_363", "mux_decoder_pixel_347", "mux_decoder_pixel_331", "mux_decoder_pixel_315", "mux_decoder_pixel_299", "mux_decoder_pixel_283", 
                             "mux_decoder_pixel_267", "mux_decoder_pixel_251", "mux_decoder_pixel_235", "mux_decoder_pixel_219", "mux_decoder_pixel_203", "mux_decoder_pixel_187", "mux_decoder_pixel_171", 
                             "mux_decoder_pixel_155", "mux_decoder_pixel_139", "mux_decoder_pixel_123", "mux_decoder_pixel_107", "mux_decoder_pixel_91", "mux_decoder_pixel_75", "mux_decoder_pixel_59", 
                             "mux_decoder_pixel_43", "mux_decoder_pixel_27", "mux_decoder_pixel_11", "mux_decoder_pixel_506", "mux_decoder_pixel_490", "mux_decoder_pixel_474", "mux_decoder_pixel_458", 
                             "mux_decoder_pixel_442", "mux_decoder_pixel_426", "mux_decoder_pixel_410", "mux_decoder_pixel_394", "mux_decoder_pixel_378", "mux_decoder_pixel_362", "mux_decoder_pixel_346", 
                             "mux_decoder_pixel_330", "mux_decoder_pixel_314", "mux_decoder_pixel_298", "mux_decoder_pixel_282", "mux_decoder_pixel_266", "mux_decoder_pixel_250", "mux_decoder_pixel_234", 
                             "mux_decoder_pixel_218", "mux_decoder_pixel_202", "mux_decoder_pixel_186", "mux_decoder_pixel_170", "mux_decoder_pixel_154", "mux_decoder_pixel_138", "mux_decoder_pixel_122", 
                             "mux_decoder_pixel_106", "mux_decoder_pixel_90", "mux_decoder_pixel_74", "mux_decoder_pixel_58", "mux_decoder_pixel_42", "mux_decoder_pixel_26", "mux_decoder_pixel_10", 
                             "mux_decoder_pixel_505", "mux_decoder_pixel_489", "mux_decoder_pixel_473", "mux_decoder_pixel_457", "mux_decoder_pixel_441", "mux_decoder_pixel_425", "mux_decoder_pixel_409", 
                             "mux_decoder_pixel_393", "mux_decoder_pixel_377", "mux_decoder_pixel_361", "mux_decoder_pixel_345", "mux_decoder_pixel_329", "mux_decoder_pixel_313", "mux_decoder_pixel_297", 
                             "mux_decoder_pixel_281", "mux_decoder_pixel_265", "mux_decoder_pixel_249", "mux_decoder_pixel_233", "mux_decoder_pixel_217", "mux_decoder_pixel_201", "mux_decoder_pixel_185", 
                             "mux_decoder_pixel_169", "mux_decoder_pixel_153", "mux_decoder_pixel_137", "mux_decoder_pixel_121", "mux_decoder_pixel_105", "mux_decoder_pixel_89", "mux_decoder_pixel_73", 
                             "mux_decoder_pixel_57", "mux_decoder_pixel_41", "mux_decoder_pixel_25", "mux_decoder_pixel_9", "mux_decoder_pixel_504", "mux_decoder_pixel_488", "mux_decoder_pixel_472", 
                             "mux_decoder_pixel_456", "mux_decoder_pixel_440", "mux_decoder_pixel_424", "mux_decoder_pixel_408", "mux_decoder_pixel_392", "mux_decoder_pixel_376", "mux_decoder_pixel_360", 
                             "mux_decoder_pixel_344", "mux_decoder_pixel_328", "mux_decoder_pixel_312", "mux_decoder_pixel_296", "mux_decoder_pixel_280", "mux_decoder_pixel_264", "mux_decoder_pixel_248", 
                             "mux_decoder_pixel_232", "mux_decoder_pixel_216", "mux_decoder_pixel_200", "mux_decoder_pixel_184", "mux_decoder_pixel_168", "mux_decoder_pixel_152", "mux_decoder_pixel_136", 
                             "mux_decoder_pixel_120", "mux_decoder_pixel_104", "mux_decoder_pixel_88", "mux_decoder_pixel_72", "mux_decoder_pixel_56", "mux_decoder_pixel_40", "mux_decoder_pixel_24", 
                             "mux_decoder_pixel_8", "mux_decoder_pixel_503", "mux_decoder_pixel_487", "mux_decoder_pixel_471", "mux_decoder_pixel_455", "mux_decoder_pixel_439", "mux_decoder_pixel_423", 
                             "mux_decoder_pixel_407", "mux_decoder_pixel_391", "mux_decoder_pixel_375", "mux_decoder_pixel_359", "mux_decoder_pixel_343", "mux_decoder_pixel_327", "mux_decoder_pixel_311", 
                             "mux_decoder_pixel_295", "mux_decoder_pixel_279", "mux_decoder_pixel_263", "mux_decoder_pixel_247", "mux_decoder_pixel_231", "mux_decoder_pixel_215", "mux_decoder_pixel_199", 
                             "mux_decoder_pixel_183", "mux_decoder_pixel_167", "mux_decoder_pixel_151", "mux_decoder_pixel_135", "mux_decoder_pixel_119", "mux_decoder_pixel_103", "mux_decoder_pixel_87", 
                             "mux_decoder_pixel_71", "mux_decoder_pixel_55", "mux_decoder_pixel_39", "mux_decoder_pixel_23", "mux_decoder_pixel_7", "mux_decoder_pixel_502", "mux_decoder_pixel_486", 
                             "mux_decoder_pixel_470", "mux_decoder_pixel_454", "mux_decoder_pixel_438", "mux_decoder_pixel_422", "mux_decoder_pixel_406", "mux_decoder_pixel_390", "mux_decoder_pixel_374", 
                             "mux_decoder_pixel_358", "mux_decoder_pixel_342", "mux_decoder_pixel_326", "mux_decoder_pixel_310", "mux_decoder_pixel_294", "mux_decoder_pixel_278", "mux_decoder_pixel_262", 
                             "mux_decoder_pixel_246", "mux_decoder_pixel_230", "mux_decoder_pixel_214", "mux_decoder_pixel_198", "mux_decoder_pixel_182", "mux_decoder_pixel_166", "mux_decoder_pixel_150", 
                             "mux_decoder_pixel_134", "mux_decoder_pixel_118", "mux_decoder_pixel_102", "mux_decoder_pixel_86", "mux_decoder_pixel_70", "mux_decoder_pixel_54", "mux_decoder_pixel_38", 
                             "mux_decoder_pixel_22", "mux_decoder_pixel_6", "mux_decoder_pixel_501", "mux_decoder_pixel_485", "mux_decoder_pixel_469", "mux_decoder_pixel_453", "mux_decoder_pixel_437", 
                             "mux_decoder_pixel_421", "mux_decoder_pixel_405", "mux_decoder_pixel_389", "mux_decoder_pixel_373", "mux_decoder_pixel_357", "mux_decoder_pixel_341", "mux_decoder_pixel_325", 
                             "mux_decoder_pixel_309", "mux_decoder_pixel_293", "mux_decoder_pixel_277", "mux_decoder_pixel_261", "mux_decoder_pixel_245", "mux_decoder_pixel_229", "mux_decoder_pixel_213", 
                             "mux_decoder_pixel_197", "mux_decoder_pixel_181", "mux_decoder_pixel_165", "mux_decoder_pixel_149", "mux_decoder_pixel_133", "mux_decoder_pixel_117", "mux_decoder_pixel_101", 
                             "mux_decoder_pixel_85", "mux_decoder_pixel_69", "mux_decoder_pixel_53", "mux_decoder_pixel_37", "mux_decoder_pixel_21", "mux_decoder_pixel_5", "mux_decoder_pixel_500", 
                             "mux_decoder_pixel_484", "mux_decoder_pixel_468", "mux_decoder_pixel_452", "mux_decoder_pixel_436", "mux_decoder_pixel_420", "mux_decoder_pixel_404", "mux_decoder_pixel_388", 
                             "mux_decoder_pixel_372", "mux_decoder_pixel_356", "mux_decoder_pixel_340", "mux_decoder_pixel_324", "mux_decoder_pixel_308", "mux_decoder_pixel_292", "mux_decoder_pixel_276", 
                             "mux_decoder_pixel_260", "mux_decoder_pixel_244", "mux_decoder_pixel_228", "mux_decoder_pixel_212", "mux_decoder_pixel_196", "mux_decoder_pixel_180", "mux_decoder_pixel_164", 
                             "mux_decoder_pixel_148", "mux_decoder_pixel_132", "mux_decoder_pixel_116", "mux_decoder_pixel_100", "mux_decoder_pixel_84", "mux_decoder_pixel_68", "mux_decoder_pixel_52", 
                             "mux_decoder_pixel_36", "mux_decoder_pixel_20", "mux_decoder_pixel_4", "mux_decoder_pixel_499", "mux_decoder_pixel_483", "mux_decoder_pixel_467", "mux_decoder_pixel_451", 
                             "mux_decoder_pixel_435", "mux_decoder_pixel_419", "mux_decoder_pixel_403", "mux_decoder_pixel_387", "mux_decoder_pixel_371", "mux_decoder_pixel_355", "mux_decoder_pixel_339", 
                             "mux_decoder_pixel_323", "mux_decoder_pixel_307", "mux_decoder_pixel_291", "mux_decoder_pixel_275", "mux_decoder_pixel_259", "mux_decoder_pixel_243", "mux_decoder_pixel_227", 
                             "mux_decoder_pixel_211", "mux_decoder_pixel_195", "mux_decoder_pixel_179", "mux_decoder_pixel_163", "mux_decoder_pixel_147", "mux_decoder_pixel_131", "mux_decoder_pixel_115", 
                             "mux_decoder_pixel_99", "mux_decoder_pixel_83", "mux_decoder_pixel_67", "mux_decoder_pixel_51", "mux_decoder_pixel_35", "mux_decoder_pixel_19", "mux_decoder_pixel_3", 
                             "mux_decoder_pixel_498", "mux_decoder_pixel_482", "mux_decoder_pixel_466", "mux_decoder_pixel_450", "mux_decoder_pixel_434", "mux_decoder_pixel_418", "mux_decoder_pixel_402", 
                             "mux_decoder_pixel_386", "mux_decoder_pixel_370", "mux_decoder_pixel_354", "mux_decoder_pixel_338", "mux_decoder_pixel_322", "mux_decoder_pixel_306", "mux_decoder_pixel_290", 
                             "mux_decoder_pixel_274", "mux_decoder_pixel_258", "mux_decoder_pixel_242", "mux_decoder_pixel_226", "mux_decoder_pixel_210", "mux_decoder_pixel_194", "mux_decoder_pixel_178", 
                             "mux_decoder_pixel_162", "mux_decoder_pixel_146", "mux_decoder_pixel_130", "mux_decoder_pixel_114", "mux_decoder_pixel_98", "mux_decoder_pixel_82", "mux_decoder_pixel_66", 
                             "mux_decoder_pixel_50", "mux_decoder_pixel_34", "mux_decoder_pixel_18", "mux_decoder_pixel_2", "mux_decoder_pixel_497", "mux_decoder_pixel_481", "mux_decoder_pixel_465", 
                             "mux_decoder_pixel_449", "mux_decoder_pixel_433", "mux_decoder_pixel_417", "mux_decoder_pixel_401", "mux_decoder_pixel_385", "mux_decoder_pixel_369", "mux_decoder_pixel_353", 
                             "mux_decoder_pixel_337", "mux_decoder_pixel_321", "mux_decoder_pixel_305", "mux_decoder_pixel_289", "mux_decoder_pixel_273", "mux_decoder_pixel_257", "mux_decoder_pixel_241", 
                             "mux_decoder_pixel_225", "mux_decoder_pixel_209", "mux_decoder_pixel_193", "mux_decoder_pixel_177", "mux_decoder_pixel_161", "mux_decoder_pixel_145", "mux_decoder_pixel_129", 
                             "mux_decoder_pixel_113", "mux_decoder_pixel_97", "mux_decoder_pixel_81", "mux_decoder_pixel_65", "mux_decoder_pixel_49", "mux_decoder_pixel_33", "mux_decoder_pixel_17", 
                             "mux_decoder_pixel_1" ]

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
        
        # Check whether all of Mux Control values are zero; if all zero, use mux_decoder_pixel_master instead of 512 zero'd XML tags
        # Assume all 512 values are zero
        bMuxControlAllZero = True
        print "before:", bMuxControlAllZero
        
        # Loop over all 512 values..
        for i in range(512):
            # Is this decoder nonzero?
            if scList[i] > 0:
                bMuxControlAllZero = False
        print "after: ", bMuxControlAllZero
                
        # Mux Control configuration: If only zero value detected..
        if bMuxControlAllZero:
            print "True"
            # ..Only populate Master
            stringList.append( '''   <mux_decoder_pixel_master count=0>''' )
        else:
            print "False"
            # ..else populate all 512 keys
            for idx in range(512):
                stringList.append( '''   <%s''' % ExtractSlowControlParamsFromFile.muxDecoderLookupTable[idx] +''' count=%i>''' % scList[0+idx] )
            
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
        """ display section by section the values already extracted from slow control configuration file (not an XML file!) """
        
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
        
    def createMuxDecoderDictKeysAndLookupTable(self):
        """ this function is used to produce the lookup table required for the mux_decoder_pixel_XX tags
            there are 512 these (not counting the master one) and this function is only likely to be run 1-2 times at most
        """
        filename = '/u/ckd27546/lpd_workspace/workspace_temp/LpdCommandSequence/scMuxDictKeys.txt'
        try:
            lookup_file = open(filename, 'w')
        except Exception as errNo:
            print "createMuxDecoderDictKeysAndLookupTable: Couldn't open file because: ", errNo
        
        # Create number in order for mux decoder pixels
        numberList = []
        for row in range(16):
            for col in range(512-row, 0,-16):
                numberList.append(col)
        
        lookupTableList = []
        mux_offset = 0x03
        pixels = 512
        
        # Generate dictionary keys to be used inside LpdSlowCtrlSequence.py
        for idx in range(pixels):
            lookupTableList.append( """                         'mux_decoder_pixel_%i'""" % numberList[idx] + """        : 0x%03x,\n""" % (mux_offset + idx*3) )
        
        # Each line should look similar to this:
        """                         'mux_decoder_pixel_512'        : 0x03,"""
        
        # Write these dictionary keys to file
        for idx in range(pixels):
            lookup_file.write( lookupTableList[idx] )
        
        try:
            lookup_file.close()
        except Exception as errNo:
            print "createdMuxDecoderTable: Couldn't close file because: ", errNo

    
        """ create the lookup table for Mux Decoder settings that will be used inside  this script """

        filename = '/u/ckd27546/lpd_workspace/workspace_temp/LpdCommandSequence/scMuxLookupTable.txt'
        try:
            lookup_file = open(filename, 'w')
        except Exception as errNo:
            print "createMuxDecoderDictKeysAndLookupTable: Couldn't open 2nd file because: ", errNo
        
        # Preamble..
        lookup_file.write("muxDecoderLookupTable = [")
        
        ''' Extract 'mux_decoder_pixel_' section from each key name.. '''
        for idx in range(pixels):    # Remove leading whitespaces
            noPreSpaces = lookupTableList[idx].strip()
            # Select key name
            keyName = noPreSpaces[0:24]
            # Remove apostrophies
            noApos = keyName.replace("'", "")
            # Remove remaining whitespaces
            noSpaces = noApos.replace(" ", "")
            # Write keyname to file
            lookup_file.write( "\"" + noSpaces + "\", ")
        # Close list with ] ..
        lookup_file.write("]")    
        
        # The list should similar to this:
        '''["mux_decoder_pixel_512", "mux_decoder_pixel_496",...'''
        
        try:
            lookup_file.close()
        except Exception as errNo:
            print "createMuxDecoderDictKeysAndLookupTable: Couldn't close 2nd file because: ", errNo
        

if __name__ == "__main__":
    slowControlParams = ExtractSlowControlParamsFromFile()
    slow_ctrl_data, list_length = slowControlParams.readSlowControlFileintoFormattedList('/u/ckd27546/lpd_workspace/workspace_temp/LpdCommandSequence/SlowCtrlCmds.txt')
    
    # Display section by section the slow control values extracted from the file above
#    slowControlParams.displayFormattedList(slow_ctrl_data, list_length)
#
    ''' Convert these into an XML file - work in progress - Currently only handles:
        * Mux Control
        * Bias Control 
    
    '''
    print "Calling convertListIntoXmlFile().."
    slowControlParams.convertListIntoXmlFile(slow_ctrl_data)
    print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"

    ''' 'Create dictionary keys and the lookup table required for mux_decoder_pixel_xxx (used by LpdSlowCtrlSequence.py and this script)
        DONE ''' 
#    slowControlParams.createMuxDecoderDictKeysAndLookupTable()
    
    
    
    
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
        