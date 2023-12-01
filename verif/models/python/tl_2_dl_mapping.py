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
import xlsxwriter as xls

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
    
    # Number of phases based on Rate
    P = get_num_phases(R)
    
    # Define Lane Bit Counters 
    lane_bit_counters = np.zeros((L, 1), dtype=np.uint32)
    
    # Define lane wise insert index which keeps track of
    # where the next insert should happen. This is mainly
    # used when you want have partial fills of the 64 bit
    # word.
    lane_nib_idx = np.full((L, 1), 16, dtype=np.uint32)
    #print(lane_byte_idx) 

    # create an empty list for each lane. Every row in each
    # lane will be a 64 bit word.
    lane = [[] for i in range(L)]
    
    # samp stores the bytes that make up the 64 bit word. This
    # is also a list of lists. The super-list is of size L because
    # for every cycle you will be sequencing in the bytes from a part
    # of the input parallel bus that will feed a particular lane. 
    # Only when the "samp" buffer for that lane has reached 64 bits
    # do we say that this is a valid cycle. 
    samp = [['x']*16 for i in range(L)]

    for r in inSamp:
        # First reshape the row such that the number of rows
        # is the number of lanes. This way we can think of each
        # row feeding a lane. Makes visualizing and processing
        # easier. To understand this, inSamp rows is the full bus which
        # is made up of all the converters, the samples, the bytes and the phases.
        # You want to break them up into L sections so that each section is now 
        # feeding into its respective lane.
        
        list_len = int(len(r))
        x = np.reshape(r, (L, int(list_len/L)))
        #print("nib index: ", lane_nib_idx)
        #print("x: ", x)
        for l in reversed(range(L)):
            ## Now that the row is split into L subrows, feed each
            ## sub-row into each lane. A valid sample is only
            ## when 64 bits have been accumulated
            x_ind = x[l].size
            for b in reversed(range(16)):
                if x[l][0] == 'x': #Case where the sample is not valid, skip the whole processing
                    break
                if x_ind > 0 :
                    samp[l][lane_nib_idx[l][0]-1] = x[l][x_ind-1]  # 0 idx because lanenibidx is a list
                                                                    # of lists where is each sub-list of length 1.
                    x_ind = x_ind - 1
                    lane_nib_idx[l] = lane_nib_idx[l] - 1
                    lane_bit_counters[l] += 4
                    if lane_bit_counters[l] == 64:
                        break

            # The above for loop for nibbles cycles through
            # nibbles in the sample. If the lane bit counter
            # reaches 64 bits, it will break out, otherwise
            # it will loop through all the nibbles. Now we 
            # check if we reached 64 bits. If we did then
            # this is a valid cycle, else just put in 'x'
            
            #print('Lane: ', l, 'Samp: ', samp[l], 'Lane Counter: ', lane_bit_counters[l])
            
            # You have to append a copy otherwise its just a pointer in python.
            lane[l].append(samp[l].copy())
            
            #print(lane[l])
            
            if lane_bit_counters[l] == 64:
               
                # Reset the counter
                lane_bit_counters[l]    = 0
                lane_nib_idx[l]        = int(16) 
                # append the sample

                # reset the sample
                samp[l] = ['x']*16
                #print(x_ind)
                # buffer the remaining bytes of the
                # current sample if any remaining
                if (x_ind > 0):
                    for bs in reversed(range(0, x_ind)):
                        if x[l][0] == 'x': #Case where the sample is not valid, skip the whole processing
                            break
                        
                        samp[l][lane_nib_idx[l][0]-1] = x[l][bs]
                        lane_nib_idx[l] = lane_nib_idx[l] - 1
                        lane_bit_counters[l] += 4
                    # For remaining bytes just put 'x'
                    #for bs in reversed(range(0, 16 - x_ind)):
                    #    samp[l].insert(0, 'x')


            
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
        #print(lane[l])
        print_table(l, R, M, Np, lane[l], 'lseq', "LSEQ OUTPUT")
    
    return lane


# @@@@@@@@@@@@@@@ END OF LSEQ_V2 Function


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
    print_table(0, R, M, prec, in_data, 's2w', "===== Raw Samples to Converter Samples =====")

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
    """
    This function provides rows of samples according to M, R and prec.
    The nSamp variable is expanded to oSamp based on rates (because we can
    have invalid cycles where the samples are invalid). 
    """

    nNibbles        = int(prec/4)
    strb_ind        = get_strb_pattern(R)
    P               = get_num_phases(R)
    in_data         = []
    si              = 0 # true Sample Index
    
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
                    for n in reversed(range(nNibbles)):
                        samp = 'M' + str(m) + '_P' + str(p) + '_' + 's' + str(si) + '_' + 'n' + str(n)
                        literal.append(samp)
            in_data.append(literal)
            si = si + 1
        else:
            in_data.append(['x'] * M * nNibbles * P)

    return in_data




def get_num_phases(R):
    '''
    Depending on the rate we will need either 1 or 2 phases.
    R: Rate
          1: 122.88 MHz
          2: 245.76 MHz
          3. 368.64 MHz
          4: 491.52 MHz
          6: 737.28 MHz
          8: 983.04 MHz
    '''

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

def print_table(Lid, R, M, prec, in_data, block, mesg=''):
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
    block: The function handles tables for various blocks in the design.
    mesg: Any message you would like to print before the table gets printed
    """
    nNibbles = int(prec/4)
    inTab = PrettyTable()
    fields = []
    
    # Get the number of phases based in rate
    P = get_num_phases(R)

    # For the header of the table.
    if(block == 's2w'):
        for m in reversed(range(M)):
            for p in reversed(range(P)):
                for n in reversed(range(nNibbles)):
                    title = 'M' + str(m) + '_P' + str(p) + '_' + 'N' + str(n)
                    fields.append(title)
                    

        #Print the table
        print(mesg)
        print("============= Parameters")
        print("Number of Converters: ", M)
        print("Number of phases: ", P)
        print("Precision: ", prec)
        print("Sampling Rate: ", get_sample_rate(R), "MSps")
        print("Clock Rate: 491.52 MHz")
    elif(block == 'lseq'):
        title = ['63:60', '59:56', '55:52', '51:48', '47:44', '43:40', '39:36', '35:32', '31:28', '27:24', '23:20', '19:16', '15:12', '11:8', '7:4', '3:0']
        for t in range(16):
            fields.append(title[t])

    
    # Add the header and the rows
    inTab.field_names = fields
    for row in in_data:
        inTab.add_row(row)
    
    # Print the table
    print(inTab)

def xls_sheet_conv_if(wb, M, prec, in_data, xls_start_row, xls_start_col, ws_name):
    '''
    This function will write the converter interface nibble literals into 
    the worksheet. Note that in_data is given as such that the rows are
    clock cycles and the columns are converter samples. Its also set in
    big endian notation. in_data is a list of lists.  
    '''
    
    ws = wb.add_worksheet(ws_name)
    
    cell_format = wb.add_format()
    #cell_format.set_bold(True)
    #cell_format.set_bg_color('yellow')
    cell_format.set_center_across()
    
    merge_format = wb.add_format({
    'bold':     True,
    'border':   6,
    'align':    'center',
    'valign':   'vcenter',
    'fg_color': '#D7E4BC',
    })
    
    # First figure out the number of headers depending on M
    header = []
    for m in range(M):
        text = "M" + str(m)
        header.append(text)
    
    # Number of nibbles will dictate how many cells need to be merged
    # for the header
    num_nibbles = int(prec/4);
    
    fr = int(xls_start_row);
    fc = int(xls_start_col);
    lc = int(xls_start_col);
    
    for h in range(len(header)):
        lr = fr + num_nibbles - 1;
        ws.merge_range(fr, fc, lr, lc, header[h], merge_format)
        fr = lr + 1
    
    for r in in_data:
        fr = xls_start_row;
        fc = fc + 1
        for s in reversed(r):
            ws.write(fr, fc, s, cell_format)
            fr = fr+1
    

def xls_sheet_lane_if(wb, L, prec, in_data, xls_start_row, xls_start_col, ws_name):
    '''
    This function will write the lane interface nibble literals into 
    the worksheet. in_data is a list of lists. The sublist is made up of
    elements that correspond to a clock cycle. 
    '''
    
    ws = wb.add_worksheet(ws_name)
    
    cell_format = wb.add_format()
    #cell_format.set_bold(True)
    #cell_format.set_bg_color('yellow')
    cell_format.set_center_across()
    
    merge_format = wb.add_format({
    'bold':     True,
    'border':   6,
    'align':    'center',
    'valign':   'vcenter',
    'fg_color': '#D7E4BC',
    })
    
    # First figure out the number of headers depending on M
    header = []
    for l in reversed(range(L)):
        text = "L" + str(l)
        header.append(text)
    
    # Number of nibbles will dictate how many cells need to be merged
    # for the header
    num_nibbles = int(prec/4);
    
    fr = int(xls_start_row);
    fc = int(xls_start_col);
    lc = int(xls_start_col);
    
    for h in range(len(header)):
        lr = fr + num_nibbles - 1;
        ws.merge_range(fr, fc, lr, lc, header[h], merge_format)
        fr = lr + 1
    
    ln_idx = 0
    for l in in_data:
        row_start_idx = xls_start_row + ln_idx * num_nibbles
        fc = xls_start_col
        for s in l: 
            fc = fc + 1
            fr = row_start_idx
            for n in reversed(s):
                ws.write(fr, fc, n, cell_format)
                fr = fr + 1
        
        # Increment column only if last last lane has been processed
        ln_idx += 1
        
    
    
            
###############################
#       MAIN FUNCTION
###############################

if __name__ == "__main__":

    # Variables
    
    Np = 16 
    M = 8 
    L = 16

    '''
    R:  Sampling rate.
        1: 122.88 MHz
        2: 245.76 MHz
        3. 368.64 MHz
        4: 491.52 MHz
        6: 737.28 MHz
        8: 983.04 MHz
    '''
    R = 8 
    
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
    
    # XLSX workbook
    book_name = "M_" + str(M) + "_L_" + str(L) + "_Np_" + str(Np) + "_R_" + str(int(get_sample_rate(R))) + ".xlsx"
    xls_row_idx = 5
    xls_col_idx = 5
    wb = xls.Workbook(book_name)
    
    
    # Prepare input to block
    in_samples = s2w(nSamp, R, M, 16)
    xls_sheet_conv_if(wb, M, 16, in_samples, 5, 5, "Converter Interface")
    
    # Output of s2w_block
    s2w_out = s2w(nSamp, R, M, Np)
    xls_sheet_conv_if(wb, M, Np, s2w_out, 5, 5, "Nibble Group Output")
    
    # lseq
    lane_out = lseq_v2(s2w_out, L, M, R)
    xls_sheet_lane_if(wb, L, 64, lane_out, 5, 5, "Lane Output")
     
    wb.close()