## Created By: Sai Mohan Kilambi
## Description:
## This is a constraint solver that gets a list of CCs that meet a given 
## constraint. So for instance if the constraint is that number of CCs should
## add up to 100 MHz, then the solver will select a list of ccs that give
## the total BW as 100 MHz.

from constraint import *
import numpy as np
import xlsxwriter as xls

# This function adds a worksheet for each TRX and num CC
# combination
def add_ws(wb, num_ccs, num_trx):
    sheet_name = str(num_trx) + 'T' + str(num_trx) + 'R_' + 'NCC_' + str(num_ccs)
    worksheet = wb.add_worksheet(sheet_name)
    return worksheet

# Add a row to the sheet
def add_xls_row(wb, ws, xls_row_idx, xls_col_idx, cc, ccfs, min_fs, s, l, f_octet, lane_rate):
    
    cell_format = wb.add_format()
    cell_format.set_center_across()
     
    for i in cc:
        ws.write(xls_row_idx, xls_col_idx, i, cell_format)
        xls_col_idx = xls_col_idx + 1 
    
    for i in ccfs:
        ws.write(xls_row_idx, xls_col_idx, i, cell_format)
        xls_col_idx = xls_col_idx + 1  
    
    ws.write(xls_row_idx, xls_col_idx, min_fs, cell_format)
    xls_col_idx = xls_col_idx + 1 
    
    for i in s:
        ws.write(xls_row_idx, xls_col_idx, i, cell_format)
        xls_col_idx = xls_col_idx + 1   
    
    ws.write(xls_row_idx, xls_col_idx, l, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    ws.write(xls_row_idx, xls_col_idx, f_octet, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    ws.write(xls_row_idx, xls_col_idx, f_octet*8, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    ws.write(xls_row_idx, xls_col_idx, lane_rate, cell_format)
    xls_col_idx = xls_col_idx + 1       

# Add sheet header and headings
def add_xls_sheet_header(wb, ws, xls_row_idx, xls_col_idx, num_trx, num_ccs, M, N_prime):
    

    cell_format = wb.add_format()
    cell_format.set_bold(True)
    cell_format.set_bg_color('yellow')
    cell_format.set_center_across()
    
    ws.write('A1', 'Num TRX')
    ws.write('B1', num_trx)
    
    ws.write('A2', 'Max Num CCs')
    ws.write('B2', num_ccs)
    
    ws.write('A3', 'I/Q')
    ws.write('B3', 2)
    
    ws.write('A4', 'Physical Converters (M)')
    ws.write('B4', M)
    
    ws.write('A5', 'N Prime (bits)')
    ws.write('B5', N_prime)
    
    ws.write('A6', 'Notes')
    ws.write('A7', '1) A CC bandwidth of 0 means its not present')
    ws.write('A8', '2) A Oversample Ratio S of 0 means its not present')
    
    for i in range(num_ccs):
        text = 'cc' + str(i) + ' (MHz)'
        ws.write(xls_row_idx, xls_col_idx, text, cell_format)
        xls_col_idx = xls_col_idx + 1 
    
    for i in range(num_ccs):
        text = 'cc' + str(i) + '_Fs (MSps)'
        ws.write(xls_row_idx, xls_col_idx, text, cell_format)
        xls_col_idx = xls_col_idx + 1  
    
    text = 'Min Fs'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx + 1 
    
    for i in range(num_ccs):
        text = 'cc' + str(i) + '_S'
        ws.write(xls_row_idx, xls_col_idx, text, cell_format)
        xls_col_idx = xls_col_idx + 1   
    
    text = 'L'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    text = 'F (octets)'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    text = 'F (bits)'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx + 1
    
    text = 'Lane Rate (Gbps)'
    ws.write(xls_row_idx, xls_col_idx, text, cell_format)
    xls_col_idx = xls_col_idx + 1      

# This function will return a list of dictionaries. 
# Each element in the list will be num_ccs number of CC's that
# will add up to the bw_constraint provided
def get_ccs(num_ccs=2, bw_constraint=100):

    # Check input parameter valid values
    if(num_ccs > 16 or num_ccs < 1):
        exit("Num CCs should be less than 16")
        
    problem = Problem()
    list_of_cc_bws = [0,5,10,15,20,25,30,35,40,45,50,60,70,80,90,100,200,400]
    for i in range(num_ccs):
        problem.addVariable("cc"+str(i), list_of_cc_bws)
    
    match num_ccs:
        case 1: 
            problem.addConstraint(lambda cc0: cc0 == bw_constraint)
        case 2: 
            problem.addConstraint(lambda cc0, cc1: cc0 + cc1 == bw_constraint)
        case 3: 
            problem.addConstraint(lambda cc0, cc1, cc2: cc0 + cc1 + cc2 == bw_constraint) 
        case 4: 
            problem.addConstraint(lambda cc0, cc1, cc2, cc3: cc0 + cc1 + cc2 + cc3 == bw_constraint)
        case 5: 
            problem.addConstraint(lambda cc0, cc1, cc2, cc3, cc4: cc0 + cc1 + cc2 + cc3 + cc4 == bw_constraint)
        case 6: 
            problem.addConstraint(lambda cc0, cc1, cc2, cc3, cc4, cc5: cc0 + cc1 + cc2 + cc3 + cc4 + cc5 == bw_constraint)
    solutions = problem.getSolutions()
    
    # Now iterate through the list and extract values in the form of a list and store them
    ccs_sorted = []
    for dict in solutions:
        ccs = list(dict.values())
        ccs.sort()
        ccs_sorted.append(ccs)
    
    ccs_sorted.sort()
    
    # Remove all duplicates from the list of lists
    ccs_unique = []
    for elem in ccs_sorted:
        if elem not in ccs_unique:
            ccs_unique.append(elem)
        
    #print(ccs_unique)
    
    return ccs_unique

if __name__ == "__main__":
   
    # Variables that dictate the table creation
    # Number of TRX (this should be a list for an exhastive table)
    # One can also think of this as the number of physical converters
    # albeit not necessarily. 
    n_trx = [2, 4]
    # Number of CCs (this should be a list for an exhaustive table)
    n_ccs = [2]
    # Composite bandwidth requirement (in MHz)
    tot_bw = 100
    # Number of SERDES lanes (this should be a list of possible Lane configurations)
    L = [2, 4, 8, 16]
    
    # Fixed bit width 
    N_prime = 16 #bits
    
    # XLSX worksheet
    wb = xls.Workbook('JESD_Calculations.xlsx')
    
    
    # Create a dictionary of sampling rates
    dict_fs = {0: 0, 5: 7.68, 10: 15.36, 15: 15.36, 20: 30.72, 
               25: 30.72, 30: 30.72, 35: 61.44, 40: 61.44, 
               45: 61.44, 50: 61.44, 60: 61.44, 70: 122.88, 
               80: 122.88, 90: 122.88, 100: 122.88, 200: 122.88, 
               400: 122.88}
    
    # Iterate over every "number of TRX Anennas"
    for trx in n_trx:
        # Within this iterate over every CC combination we want to support
        for ccs in n_ccs:
            xls_sheet_row = 11
            xls_sheet_col = 4
             
            # Add a sheet to the workbook
            ws = add_ws(wb, ccs, trx)
            
            # Definition of M as per the standard is the number of converters
            M = trx 
            
            # Add Header information to the worksheet
            add_xls_sheet_header(wb, ws, xls_sheet_row-2, xls_sheet_col, trx, ccs, M, N_prime)
            
            # Calculate all CC Combinations that add up to tot_bw
            list_cc_comb = get_ccs(ccs, tot_bw)
            # For every CC combination generate a correponding list of 
            # sampling rates and Oversampling Ratios S.
            for cc_comb in list_cc_comb: 
                list_fs =  [dict_fs[x] for x in cc_comb]
                #print(list_fs)
                # Find the minimum sampling rate greater than 0
                # We are avoiding 0 because, 0 means this CC is not
                # present
                min_fs = min(i for i in list_fs if i > 0)
                #print(min_fs)
                
                # Generate Oversampling list
                list_S = [fs/min_fs for fs in list_fs]
                #print(list_S)
                
                # Logical number of converters (note that the logical
                # number of converters is the sum total of all the over-sampling
                # ratios. Think of each poly-phase as an independent I/Q)
                Mp = trx * sum(list_S) * 2 # 2 is for IQ, Assuming ZIF architecture
                
                # Now iterate over every "Number of lanes" and figure
                # out the lane rate. 
                for lanes in L:
                    # Calculate Frame size in octets
                    F = Mp * N_prime / 8 / lanes 
                    # Calculate Lane rate
                    lane_rate = (F*8) * min_fs * (66/64) / 1000 # this is in Gbps 
                    
                    add_xls_row(wb, ws, xls_sheet_row, xls_sheet_col, cc_comb, list_fs, min_fs, list_S, lanes, F, lane_rate)
                    
                    xls_sheet_row = xls_sheet_row + 1
                    # Print
                    #print("F octets: ", int(F*8), " bits, Lanes: ", lanes, ", Rate: ", lane_rate, " Gbps")
                
    
    wb.close()
       
    

