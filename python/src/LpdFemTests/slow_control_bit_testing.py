
from string import strip, split

def read_slow_ctrl_file(filename):

    slow_ctrl_file = open(filename, 'r')
    lines = slow_ctrl_file.readlines()
    slow_ctrl_file.close()    
    
    data = []
    for line in lines:
        ivals = [int(val) for val in split(strip(line))]
        data.append(ivals)
        
    i_max = len(data)
#        j_max = len(data[0])
    
    no_words = i_max / 32
    if i_max%32:
        no_words = no_words + 1
        
    slow_ctrl_data = [0L] * no_words

    j = 0
    k = 0
    nbits = 0
    data_word = 0L;
    data_mask = 1L;
    
    for i in range(i_max):
        if data[i][1] == 1:
            nbits = nbits + 1
            if data[i][2] == 1:
                data_word = data_word | data_mask
            if j == 31:
                slow_ctrl_data[k] = data_word
                data_word = 0l
                data_mask = 1L
                k = k+1
                j = 0
            else:
                data_mask = data_mask << 1
                j = j + 1
    
    slow_ctrl_data[k] = data_word
    no_of_bits = nbits
            
    return slow_ctrl_data, no_of_bits





if __name__ == "__main__":

    slow_ctrl_data, no_of_bits = read_slow_ctrl_file( '/u/ckd27546/workspace/xfel_workspace/LpdFemTests/redundant_files/scBitTesting.txt')

    for idx in range(len(slow_ctrl_data)):
        if idx % 8 == 0:
            print "\n%3i: " % idx,
        print "%8X" % slow_ctrl_data[idx],

    print ""
