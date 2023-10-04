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
    
    text = 'M'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    
    xls_col_idx = xls_col_idx+1
    
    text = 'Lanes'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    
    xls_col_idx = xls_col_idx+1
    
    text = 'Fs (MSps)'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    
    xls_col_idx = xls_col_idx+1
    
    text = 'Lane Rate (Gbps)'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)    
    

def add_row(wb, ws, xls_row_idx, xls_col_idx, npr, m, l, fs, lane_rate):
    cell_format = wb.add_format()
    cell_format.set_center_across() 

    ws.write(xls_row_idx, xls_col_idx, npr, cell_format)
    
    xls_col_idx = xls_col_idx+1
    
    ws.write(xls_row_idx, xls_col_idx, m, cell_format)
    
    xls_col_idx = xls_col_idx+1
    
    ws.write(xls_row_idx, xls_col_idx, l, cell_format)
    
    xls_col_idx = xls_col_idx+1
    
    ws.write(xls_row_idx, xls_col_idx, fs, cell_format)
    
    xls_col_idx = xls_col_idx+1
    
    ws.write(xls_row_idx, xls_col_idx, lane_rate, cell_format)    

if __name__ == "__main__":
    
    # Variables that dictate the table creation
    
    # Encoding Rate
    enc_rate = 66/64
    
    #Number of converters
    #M = [2, 4, 8, 16]
    M = [2, 4, 8, 16]
    
    # Number of SERDES lanes (this should be a list of possible Lane configurations)
    #L = [2, 4, 8, 16]
    L = [2, 4, 8, 16]
    
    # Fixed bit width 
    N_prime = [12, 16, 24, 32, 48] #bits
    
    # Sample rates
    #Fs = 122.88*[1, 2, 4, 6, 8]
    Fs = [122.88, 245.76, 491.52, 737.28, 983.04]
   
    # Accepted Lane Rates
    lr = [8.11008, 12.16512, 16.22016, 24.33024, 32.44032]
    
    # XLSX workbook
    xls_row_idx = 5
    xls_col_idx = 5
    wb = xls.Workbook('JESD_Rates.xlsx')
    ws = wb.add_worksheet('Rates')
    
    add_xls_sheet_header(wb, ws, xls_row_idx, xls_col_idx)
   
    xls_row_idx = xls_row_idx + 2 
    for np in N_prime:
        for m in M:
            for l in L:
                for fs in Fs:
                    lane_rate = round((m * np * fs * enc_rate) / (l * 1000), 5)
                    if lane_rate in lr:
                        add_row(wb, ws, xls_row_idx, xls_col_idx, np, m, l, fs, lane_rate)
                        #print("N': ", np, "bits, M: ", m, ", Lanes: ", l, ", Fs: ", fs, "MSps, Lane Rate: ", lane_rate, " Gbps")  
                        xls_row_idx = xls_row_idx+1        
                    
    wb.close()
