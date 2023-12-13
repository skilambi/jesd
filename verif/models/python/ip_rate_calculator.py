## Created By: Sai Mohan Kilambi
## Description:
## This script calculates the rate of JESD204C lanes
## for various values of N', M, L and Fs. Below are
## the possible values for each of these variables
## N' =  {16, 24, 48}
## M  =  {2, 4, 8, 16}. Note that these are IQ converters
##       meaning they already have a factor of 2
## L  =  {2, 4, 8, 16}
## Fs =  122.88 MSPs x {1, 2, 4, 6, 8}
## An excel sheet is generated for all these combinations.
## Allowed lane rates are {8110.08, 12165.12, 16220.16, 
## 24330.24, 32550.32} Gbps. If any combination results
## in rates that are not in the allowed lane rate then 
## skip the combination.

from constraint import *
import numpy as np
import xlsxwriter as xls

def add_xls_sheet_header(wb, ws, xls_row_idx, xls_col_idx):
    

    cell_format = wb.add_format()
    cell_format.set_bold(True)
    cell_format.set_bg_color('yellow')
    cell_format.set_center_across()
    
    text = 'N\''
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    
    xls_col_idx = xls_col_idx+1
    
    text = 'Lanes'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    
    xls_col_idx = xls_col_idx+1
    
    text = 'M'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    
    xls_col_idx = xls_col_idx+1
    
    
    text = 'Fs (MSps)'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    
    xls_col_idx = xls_col_idx+1
    
    #text = 'Phases'
    #ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    
    #xls_col_idx = xls_col_idx+1 
    
    text = 'OS (Sample Rpt)'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx+1 
    
    text = 'S'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx+1 
    
    text = 'Lane Rate (Gbps)'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    
    xls_col_idx = xls_col_idx + 1

    text = 'Total Bits (F)'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    text = 'Total Bits (Impl)'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    text = 'Num Octets'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    text = 'F'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    
    text = 'Input bitwidth per lane (Impl)'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    

def add_row(wb, ws, xls_row_idx, xls_col_idx, npr, m, l, fs, lane_rate, os, s):
    cell_format = wb.add_format()
    cell_format.set_center_across() 

    ws.write(xls_row_idx, xls_col_idx, npr, cell_format)
    xls_col_idx = xls_col_idx+1
    
    ws.write(xls_row_idx, xls_col_idx, l, cell_format)
    xls_col_idx = xls_col_idx+1
    
    ws.write(xls_row_idx, xls_col_idx, m, cell_format)
    xls_col_idx = xls_col_idx+1
    
    
    ws.write(xls_row_idx, xls_col_idx, fs, cell_format)
    xls_col_idx = xls_col_idx+1
    
    #if fs > 491.52 :
    #    p = 2 
    #else : 
    #    p = 1
    
    #ws.write(xls_row_idx, xls_col_idx, p, cell_format)
    #xls_col_idx = xls_col_idx + 1
    
    ws.write(xls_row_idx, xls_col_idx, os, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    ws.write(xls_row_idx, xls_col_idx, s, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    ws.write(xls_row_idx, xls_col_idx, lane_rate, cell_format)    
    xls_col_idx = xls_col_idx + 1
    
    # The total bits here is the number of converters 
    # times S times the precision. This is independent of implementation
    # and is used in the calculation of F. 
    tot_bits_f = m * s * npr # 2 is for the number of rails
    tot_bits_impl = m * 2 * os * npr # 2 is for the number of rails
    ws.write(xls_row_idx, xls_col_idx, tot_bits_f, cell_format)    
    xls_col_idx = xls_col_idx + 1
    ws.write(xls_row_idx, xls_col_idx, tot_bits_impl, cell_format)    
    xls_col_idx = xls_col_idx + 1
    
    #Num Octets
    ws.write(xls_row_idx, xls_col_idx, tot_bits_f/8, cell_format)    
    xls_col_idx = xls_col_idx + 1
    
    # F calculation
    ws.write(xls_row_idx, xls_col_idx, tot_bits_f/8/l, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    # This is useful for implementation. How many bits are being
    # fed per clockcycle to a lane.   
    ws.write(xls_row_idx, xls_col_idx, tot_bits_impl/l, cell_format)
    xls_col_idx = xls_col_idx + 1
    

if __name__ == "__main__":
    
    # Variables that dictate the table creation
    
    # Encoding Rate
    enc_rate = 66/64
    
    #Number of converters
    #M = [2, 4, 8, 16]
    M = [2, 4, 8, 16]
    
    # Number of SERDES lanes (this should be a list of possible Lane configurations)
    #L = [2, 4, 8, 16]
    L = [1, 2, 4, 8]
    
    # Fixed bit width 
    N_prime = [12, 16, 24, 32, 48] #bits
    
    # Sample rates
    #Fs = 122.88*[1, 2, 4, 6, 8]
    Fs = [122.88, 245.76, 491.52, 737.28, 983.04]
   
    # Accepted Lane Rates
    lr = [8.11008, 12.16512, 16.22016, 24.33024, 32.44032]
    
    # Sample Repeat - Which means you repeat the same sample
    # twice. You can think of this as the converter having a
    # digital Twin.
    OS = [1, 2]
    S = [1, 2]
    
    # XLSX workbook
    xls_row_idx = 5
    xls_col_idx = 5
    wb = xls.Workbook('JESD_Rates.xlsx')
    ws = wb.add_worksheet('Rates')
    
    add_xls_sheet_header(wb, ws, xls_row_idx, xls_col_idx)
   
    xls_row_idx = xls_row_idx + 2 
    for np in N_prime:
        for l in L:
            for m in M:
                for fs in Fs:
                    for os in OS:
                        for s in S: 
                            lane_rate = round((m * os * np * fs * enc_rate) / (l * 1000), 5) # 5 is resolution.
                            print("N': ", np, "bits, M: ", m, ", Lanes: ", l, ", Fs: ", fs, "MSps, Lane Rate: ", lane_rate, " Gbps, OS: ", os, " S: ", s)  
                            F = (m*s*np/8/l)
                            
                            # You want to break if S=2 is integer but S=1 was also an integer
                            F1 = (m*np/8/l)
                            if s == 2 and F1.is_integer():
                                break
                            #print("N': ", np, "bits, M: ", m, ", Lanes: ", l, ", Fs: ", fs, "MSps, Lane Rate: ", lane_rate, " Gbps")  
                            if lane_rate in lr and F.is_integer():
                                add_row(wb, ws, xls_row_idx, xls_col_idx, np, m, l, fs, lane_rate, os, s)
                                #print("N': ", np, "bits, M: ", m, ", Lanes: ", l, ", Fs: ", fs, "MSps, Lane Rate: ", lane_rate, " Gbps")  
                                xls_row_idx = xls_row_idx+1        
                    
    wb.close()
