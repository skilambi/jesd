## Author: Sai Kilambi
## Date Created: Sept 1 2023
## Description:
#  This python script will use the JESD_Rates xls which provides
#  all the options for acceptable rates. From this we need to
#  figure out how data will be mapped into the 64 bit bus of the
#  lanes. Note this is happening after the raw converter samples
#  have been mapped into converter words. 
#
#  Some notes about notation
#  Converter is specified by M0 to M15. But since we are thinking
#  of ZIF, we can combine pairs of converters. This means we these
#  I/Q converters are in the range m0 to m7. Each raw sample from
#  each converter is N' bits and hence the size of an IQ sample is
#  2 x N'. 
#  IQ samples will be specified by m<iq converter index>_<sample index>
#  If the 64 bits contains more than one sample, we will specify this in 
#  square brackets. For instance if N'=16 bits, M=2 then 64 bits lane
#  sample will be written as:
#  [m0_1 m0_0]
#  This is the concatenation of two 32 bit sample. 

# First case of M=2, N'=16 bits and L = 2. 
# In this case 2 converter outputs (32 bit total)
# is being mapped to two lanes.  

import numpy as np
from prettytable import PrettyTable

def lseq_v2(inSamp, L, M, R):
    """
    This is a more generic version of lseq_v1. The insight here is that if you
    look at the number of converters and number of phases (due to rate), it will
    always be more than or equal to the number of lanes. This number will be a 
    multiple of the number of lanes. So actually the whole sequencing of sample
    bytes can be done in terms of loops instead of the case state method we 
    were using in v1. 
    
    Parameters:
    -----------
        inSamp: This is a list (super) of lists (sub). Every row in the super list
                can be thought of as a parallel bus word coming through. Every item
                in the sub-list is a byte belonging to the converters specified by 
                M. 
        L:      Number of programmed lanes.
        M:      Number of programmed converters.
        R:      Sampling rate.
                    1: 122.88 MHz
                    2: 245.76 MHz
                    3. 368.64 MHz
                    4: 491.52 MHz
                    6: 737.28 MHz
                    8: 983.04 MHz
    """
    
    print (" I am in V2 of LSEQ")
    # Number of phases based on Rate
    P = get_num_phases(R)
    
    # Define Lane Bit Counters 
    lane_bit_counters = np.zeros((L, 1), dtype=np.uint32)
    
    # create an empty list for each lane. Every row in each
    # lane will be a 64 bit word.
    lane = [[] for i in range(L)]
    
    # samp stores the bytes that make up the 64 bit word. This
    # is also a list of lists. The super-list is of size L because
    # for every cycle you will be sequencing in the bytes from a part
    # of the input parallel bus that will feed a particular lane. 
    # Only when the "samp" buffer for that lane has reached 64 bits
    # do we say that this is a valid cycle. 
    samp = [[] for i in range(L)]

    for r in inSamp:
        # First reshape the row such that the number of rows
        # is the number of lanes. This way we can think of each
        # row feeding a lane. Makes visualizing and processing
        # easier.
        
        list_len = int(len(r))
        x = np.reshape(r, (L, int(list_len/L)))
        for l in reversed(range(L)):
            ## Now that the row is split into two, feed each
            ## sub-row into each lane. A valid sample is only
            ## when 64 bits have been accumulated
            for b in reversed(range(x[l].size)):
                if b == 'x': #Case where the sample is not valid
                    break

                samp[l].insert(0, x[l][b])
                lane_bit_counters[l] += 8
                if lane_bit_counters[l] == 64:
                    break
            print("Lane: ", l, "Samp: ", samp[l])
            # The above for loop for bytes cycles through
            # bytes in the sample. If the lane bit counter
            # reaches 64 bits, it will break out, otherwise
            # it will loop through all the bytes. Now we 
            # check if we reached 64 bits. If we did then
            # this is a valid cycle, else just put in 'x'
            
            if lane_bit_counters[l] == 64:
               
                # Reset the counter
                lane_bit_counters[l] = 0
               
                # append the sample
                lane[l].append(samp[l])

                # reset the sample
                samp[l] = []

                # buffer the remaining bytes of the
                # current sample if any remaining
                #if (b < (x[l].size - 1)):
                if (b > 0):
                    for bs in reversed(range(0, b)):
                        samp[l].insert(0, x[l][bs])
                        lane_bit_counters[l] += 8
            else: # Didnt collect enough, so this is not a valid cycle.
                lane[l]. append(['x'] * 8)
            
    # Now pretty print the lane outputs
    print(" ***************** MODULE LSEQ OUTPUT *****************")
    print('')
    print("============= Parameters")
    print("Number of Converters: ", M)
    print("Number of Phases: ", get_num_phases(R))
    print("Number of Lanes: ", L)
    print("Precision (bits): ", 64)
    print("Sampling Rate: ", get_sample_rate(R), "MSps")
    print("Clock Rate: 491.52 MHz")
    for l in range(L):
        print("============ LANE ", l, " OUTPUT =============")
        print_table(l, R, M, Np, lane[l], 'lseq')


# @@@@@@@@@@@@@@@ END OF LSEQ_V2 Function


def lseq_v1(inSamp, L, M, R, Np, link_mode):
    """
    This function is responsible for mapping input samples coming out of the
    s2w block to lanes. 

    Parameters:
    -----------
        inSamp: This is a list (super) of lists (sub). Every row in the super list
                can be thought of as a parallel bus word coming through. Every item
                in the sub-list is a byte belonging to the converters specified by 
                M. 
        L:      Number of programmed lanes.
        M:      Number of programmed converters.
        R:      Sampling rate.
                    1: 122.88 MHz
                    2: 245.76 MHz
                    3. 368.64 MHz
                    4: 491.52 MHz
                    6: 737.28 MHz
                    8: 983.04 MHz
        Np:     Np bits: 16, 24, 32, 48
        link_mode: single (0) or dual (1) mode.
    """
    # Define Lane Bit Counters 
    lane_bit_counters = np.zeros((L, 1), dtype=np.uint32)
    # create an empty list for each lane. Every row in each
    # lane will be a 64 bit word.
    lane = [[] for i in range(L)]
    samp = [[] for i in range(L)]
    match L:
        case 2: # 2 Lanes
            match M:
                case 2: # 2 Converters
                    match R:
                        case 4: # 491.52 MSps.
                            if (link_mode == 0): #single link case
                                # M = 2, L = 2, R = 491.52
                                # In this case each converter will map
                                # to a lane. So for every row, we will 
                                # reshape it according to the number of lanes
                                for r in inSamp:
                                    list_len = int(len(r))
                                    x = np.reshape(r, (L, int(list_len/L)))
                                    # Now that the row is split into two, feed each
                                    # sub-row into each lane. A valid sample is only
                                    # when 64 bits have been accumulated
                                    for l in range(L):
                                        for b in range(x[l].size):
                                            samp[l].append(x[l][b])
                                            lane_bit_counters[l] += 8
                                            if lane_bit_counters[l] == 64:
                                                break

                                        # The above for loop for bytes cycles through
                                        # bytes in the sample. If the lane bit counter
                                        # reaches 64 bits, it will break out, otherwise
                                        # it will loop through all the bytes. Now we 
                                        # check if we reached 64 bits. If we did then
                                        # this is a valid cycle, else just put in 'x'
                                        
                                        if lane_bit_counters[l] == 64:
                                            
                                            # Reset the counter
                                            lane_bit_counters[l] = 0
                                            
                                            # append the sample
                                            lane[l].append(samp[l])

                                            # reset the sample
                                            samp[l] = []

                                            # buffer the remaining bytes of the
                                            # current sample if any remaining
                                            if (b < (x[l].size - 1)):
                                                for bs in range(b+1, x[l].size):
                                                    samp[l].append(x[l][bs])
                                                    lane_bit_counters[l] += 8

                                        else: # Didnt collect enough, so this is not a valid
                                              # cycle.
                                            lane[l]. append(['x'] * 8)


    # Now pretty print the lane outputs
    print(" ***************** MODULE LSEQ OUTPUT *****************")
    print('')
    print("============= Parameters")
    print("Number of Converters: ", M)
    print("Number of Phases: ", get_num_phases(R))
    print("Number of Lanes: ", L)
    print("Precision (bits): ", 64)
    print("Sampling Rate: ", get_sample_rate(R), "MSps")
    print("Clock Rate: 491.52 MHz")
    for l in range(L):
        print("============ LANE ", l, " OUTPUT =============")
        print_table(l, R, M, Np, lane[l], 'lseq')


                                 
def s2w(nSamp, R, M, prec):
    """ 
    S2W block is the block that converts raw samples to converter words. 
    This function can be thought of as printing out the parallel input or output
    interface to/from the block. Remember that in implementation this will be a 
    dual phase interface with each interface running at 491.52 MHz.
    Strobes will be used to mark valid samples. Since the purpose of this block
    is only to extend the precision, the same function can be used to represent
    both the input and output of this block
    Parameters:
    -----------
        nSamp:  Numeber of samples we are considering.
        R:      Rate. Multiple of 122.88 MSPs
                    1: 122.88 MHz
                    2: 245.76 MHz
                    3. 368.64 MHz
                    4: 491.52 MHz
                    6: 737.28 MHz
                    8: 983.04 MHz
        M:      Number of converters. Should be {2, 4, 8, 16}
        prec:   Precision in bits
    """
    

    # Acceptable ranges for parameters
    acceptable_R = [1, 2, 3, 4, 6, 8]
    acceptable_M = [2, 4, 8, 16]

    # Assertions to check if parameters are correct
    assert R in acceptable_R, "Rate Multiplier should be in the range: {1, 2, 3, 4, 6, 8}"
    assert M in acceptable_M, "Number of converters should be a power of 2: {2, 4, 8, 16}"

    # Get the sample list
    in_data = get_sample_pattern(nSamp, M, R, prec)

    # Print the input waveform in a beautiful way.
    # Dont need lanes for this block so set to 0.
    print_table(0, R, M, prec, in_data, 's2w')

    return in_data

def get_strb_pattern(R):
    """
    This function returns the strobe pattern given the rate. Note that
    the actual pattern returned in an index. Assumption here is that the
    clock rate is 491.52 MHz. This is a dual phase implementation. If we 
    imagine 4 cycle counter at 491.52 then the following returned index indicate
    a particular pattern.

    index = [0] means [1 0 0 0] strobe
    index = [0 2] means [1 0 1 0] strobe
    index = [0 1 2] means [ 1 1 1 0 ] strobe
    index = [0 1 2 3] means [1 1 1 1] strobe

    Single Phase:
    122.88 : 1 0 0 0 1 0 0 0
    245.76 : 1 0 1 0 1 0 1 0
    368.64 : 1 1 1 0 1 1 1 0
    491.52 : 1 1 1 1 1 1 1 1
    
    Dual Phase:
    737.28 : 1 1 1 0 1 1 1 0
    983.04 : 1 1 1 1 1 1 1 1
    """
    match R:
        case 1: # 122.88 MSPs
            strb = [0]
        case 2: # 245.76 MSPs
            strb = [0, 2]
        case 3 | 6: # 368.64 and 737.28 MSPs
            strb = [0, 1, 2]
        case 4 | 8: # 491.52 MSPs and 983.04 MSPs
            strb = [0, 1, 2, 3]

    return strb



def get_sample_pattern(nSamp, M, R, prec):

    nOctets         = int(prec/8)
    strb_ind        = get_strb_pattern(R)
    P               = get_num_phases(R)
    in_data          = []

    # the nSamp parameter is for the number
    # of samples at a given rate. But since the 
    # clock rate is 491.52 MHz, we need to adjust
    # the the number of samples based on the sampling
    # rate and clock rate. This is important to make sure that all
    # samples are covered in the analysis

    match R:
        case 1:
            osSamp = 4 * nSamp
        case 2:
            osSamp = 2 * nSamp
        case 3 | 6:
            # 4/3 because we need 4 samples
            # for every 3. The 4th sample will
            # be invalid. This is how the hardware
            # would work.
            osSamp = int((4/3) * nSamp)
        case 4 | 8:
            osSamp = nSamp

    for n in range(osSamp):
        rem     = n % 4
        samp    = '' # byte sample for every converter
        literal = [] # Entire row in the table

        if rem in strb_ind: # this is a valid cycle
            for m in reversed(range(M)):     
                for p in reversed(range(P)):
                    for b in reversed(range(nOctets)):
                        samp = 'M' + str(m) + '_P' + str(p) + '_' + 's' + str(n) + '_' + 'b' + str(b)
                        literal.append(samp)
            in_data.append(literal)
        else:
            in_data.append(['x'] * M * nOctets * P)

    return in_data




def get_num_phases(R):

    if R in [1, 2, 3, 4]:
        P = 1
    else:
        P = 2

    return P

def get_sample_rate(R):
    """
    Returns the actual sample rate given R
    Parameters:
    R: Rate
        1 = 122.88
        2 = 245.76
        3 = 368.64
        4 = 491.52
        6 = 737.28
        8 = 983.04
    """
    match R:
        case 1:
            Fs = 122.88
        case 2:
            Fs = 245.76
        case 3:
            Fs = 368.64
        case 4:
            Fs = 491.52
        case 6:
            Fs = 737.28
        case 8: 
            Fs = 983.04
    return Fs

def print_table(Lid, R, M, prec, in_data, block):
    """
    This function prints out a table with samples and byte positions.
    The printing is such that the lowest converter index is at the lower
    end. The sample is written in big-endian format
    Parameters:
    Lid: Lane ID for which table is being printed
    R : Rate
    M : Number of converters
    prec: Precising in bits
    in_data: rows to be printed
    """
    nOctets = int(prec/8)
    inTab = PrettyTable()
    fields = []
    
    # Get the number of phases based in rate
    P = get_num_phases(R)

    # For the header of the table.
    if(block == 's2w'):
        for m in reversed(range(M)):
            for p in reversed(range(P)):
                for b in reversed(range(nOctets)):
                    title = 'M' + str(m) + '_P' + str(p) + '_' + 'B' + str(b)
                    fields.append(title)
                    

        #Print the table
        print("============= Parameters")
        print("Number of Converters: ", M)
        print("Number of phases: ", P)
        print("Precision: ", prec)
        print("Sampling Rate: ", get_sample_rate(R), "MSps")
        print("Clock Rate: 491.52 MHz")
    elif(block == 'lseq'):
        title = ['63:56', '55:48', '47:40', '39:32', '31:24', '23:16', '15:8', '7:0']
        for t in range(8):
            fields.append(title[t])

    
    # Add the header and the rows
    inTab.field_names = fields
    for row in in_data:
        inTab.add_row(row)
    
    # Print the table
    print(inTab)
###############################
#       MAIN FUNCTION
###############################

if __name__ == "__main__":

    # Variables
    
    M = 4
    
    Np = 24 
    
    L = 2

    '''
    R:  Sampling rate.
        1: 122.88 MHz
        2: 245.76 MHz
        3. 368.64 MHz
        4: 491.52 MHz
        6: 737.28 MHz
        8: 983.04 MHz
    '''
    R = 4 
    
    '''
    Number of octets
    '''
    nOctets = int(Np/8)
    
    # IQ width 
    iq_width = 2 * Np
    bus_width = M * Np
    
    # Number of Samples 
    nSamp = 12 
    
    # Define Lane Bit Counters 
    lane_bit_counters = np.zeros((L, 1), dtype=np.uint32)
    
    # Prepare input to block
    in_samples = s2w(nSamp, R, M, 16)

    # Output of s2w_block
    s2w_out = s2w(nSamp, R, M, Np)

    # lseq

    #lseq_v1(s2w_out, L, M, R, Np, 0)
    lseq_v2(s2w_out, L, M, R)
    
    l = 0 # lane index
    lane = [[] for i in range(L)]
    samp = ''
    for s in in_samples:
        for b in s: #every byte in s
            if lane_bit_counters[l] == 64:
                lane[l].append(samp)
                samp = b + ' '  
                lane_bit_counters[l] = 0
                if l == L - 1:
                    l = 0
                else:
                    l = l + 1
            else:
                samp = samp + b + ' '
            #lane[l].append(b)
            lane_bit_counters[l] = lane_bit_counters[l] + 8 
                
    #Check the last sample is 64 bit...if yes just add it
    lane[l].append(samp)
                
    #print(lane[0])
    #print(lane[1])


