// This code here is to work out the pseudocode
// for LAGG block. This block gets input from
// cswp block which generates two rails 
//

//
// Parameters
//

parameter NPMAX     = 48;
parameter MMAX      = 16;
parameter MMAX_HALF = MMAX / 2;
parameter LMAX      = 8;
parameter LMAX_HALF = LMAX / 2;

parameter LSAMP_W   = 512;
parameter BLKBIT_W  = 10;

parameter NUM_RAILS = 2;
parameter MAX_OS    = 2;

parameter BUF_W     = MMAX * NPMAX * NUM_RAILS * MAX_OS

typedef logic [ BUF_W - 1 : 0 ] buf_t;
typedef logic [ MMAX - 1 : 0 ][ NPMAX - 1 : 0 ] cswp_t;
typedef logic [ BLKBIT_W - 1 : 0 ] blkw_t;
typedef logic [ LMAX - 1 : 0 ][ LSAMP_W - 1 : 0 ] lsamp_t;
typedef logic [ LMAX_HALF - 1 : 0 ][ LSAMP_W - 1 : 0 ] lsamph_t; //half the lanes, used in dual mode



//
// LAGG Port List
//

// Data Inputs

input [ MMAX - 1 : 0 ] [ NPMAX - 1 : 0 ]    i_lagg_r0               ;
input [ MMAX - 1 : 0 ] [ NPMAX - 1 : 0 ]    i_lagg_r1               ;
input [ MMAX - 1 : 0 ]                      i_strb                  ;

// CMD Interface

input logic [ 3 : 0 ]   cmd_l_0;
input logic [ 3 : 0 ]   cmd_l_1;
input logic [ 4 : 0 ]   cmd_m_0;
input logic [ 4 : 0 ]   cmd_m_1;
input logic [ 6 : 0 ]   cmd_np_0;
input logic [ 6 : 0 ]   cmd_np_1;
input logic             cmd_os_0;
input logic             cmd_os_1;
input logic             cmd_mode;

// Data Outputs

output [ LMAX - 1 : 0 ]                         o_valid             ;
output [ LMAX - 1 : 0 ] [ LSAMP_W - 1 : 0 ]     o_lsamp             ;
output [ LMAX - 1 : 0 ] [ BLKBIT_W - 1 : 0 ]    o_blk_bit_width     ;


//
// Internal Variables
//

buf_t int_buf, int_buf_d;

blkw_t blk_wdth_0, blk_wdth_0_d;
blkw_t blk_wdth_1, blk_wdth_1_d;


//
// LOGIC FOR O_VALID
//
// The idea here is that you have strobes coming in from the CSWP
// block. A strobe is common for the same converter in both rails.
// We have two cases. Single Link and Dual Link
//
// Single Link:
// Depending on he setting of cmd_m_0, the correct number of strobes
// will be OR-ed. This OR-ed strobe will be routed to the correct number
// of Lanes as specified by cmd_l_0
//
// Dual Link:
// There will be two variables here. One for the first link and the
// second for the second link. The first variable will get the OR-ing
// of cmd_m_0 number of converter strobes from the top half of the converters.
// The second variable will get the OR-ing of cmd_m_1 number of converters
// from the bottom half of the converters. The first variable will be used
// as valid for the top half of the lanes. The second variable will be
// used as the valid for the bottom half of the lanes.
//

logic lane_0_valid, lane_1_valid;

always_ff@ ( posedge clk ) begin
    if ( case_mode == 0 ) begin // Single mode Case
        case ( cmd_l_0 )
            'd1 : begin
                o_valid <= o_valid_sm_set ( lane_0_valid, 1 );
            end

            'd2 : begin
                o_valid <= o_valid_sm_set ( lane_0_valid, 2 );
            end

            'd4 : begin
                o_valid <= o_valid_sm_set ( lane_0_valid, 4 );
            end
            
            'd8 : begin
                o_valid <= o_valid_sm_set ( lane_0_valid, 8 );
            end

            default:
                o_valid <= '0;
        endcase
    end else begin // Dual Mode Case 

    
        case ( cmd_l_0 )
            'd1 : begin
                o_valid[LMAX_HALF - 1 : 0] <= o_valid_dm_set ( lane_0_valid, 1 );
            end

            'd2 : begin
                o_valid[LMAX_HALF - 1 : 0] <= o_valid_dm_set ( lane_0_valid, 2 );
            end

            'd4 : begin
                o_valid[LMAX_HALF - 1 : 0] <= o_valid_dm_set ( lane_0_valid, 4 );
            end

            default : 
                o_valid [LMAX_HALF - 1 : 0 ] <= '0;
        endcase

        case ( cmd_l_1 )
            'd1 : begin
                o_valid[LMAX - 1 : LMAX_HALF] <= o_valid_dm_set ( lane_1_valid, 1 );
            end

            'd2 : begin
                o_valid[LMAX - 1 : LMAX_HALF] <= o_valid_dm_set ( lane_1_valid, 2 );
            end

            'd4 : begin
                o_valid[LMAX - 1 : LMAX_HALF] <= o_valid_dm_set ( lane_1_valid, 4 );
            end

            default: 
                o_valid[LMAX - 1 : LMAX_HALF] <= '0;
        endcase

    end 
end

always_comb begin

    lane_0_valid = 0;
    lane_1_valid = 0;


    if ( cmd_mode == 0 ) begin // Single LINK mode

        case ( cmd_m_0 ) 
            'd2: begin
                lane_0_valid = output_valid_gen ( i_strb, 2, 0 );
            end
            'd4: begin
                lane_0_valid = output_valid_gen ( i_strb, 4, 0 );
            end
            'd8: begin
                lane_0_valid = output_valid_gen ( i_strb, 8, 0 );
            end
            'd16: begin
                lane_0_valid = output_valid_gen ( i_strb, 16, 0 );
            end
        endcase

    end else begin


        case ( cmd_m_0 ) 
            'd2: begin
                lane_0_valid = output_valid_gen ( i_strb, 2, 0 );
            end
            'd4: begin
                lane_0_valid = output_valid_gen ( i_strb, 4, 0 );
            end
            'd8: begin
                lane_0_valid = output_valid_gen ( i_strb, 8, 0 );
            end
        endcase


        case ( cmd_m_1 ) 
            'd2: begin
                lane_1_valid = output_valid_gen ( i_strb, 2, MMAX_HALF );
            end
            'd4: begin
                lane_1_valid = output_valid_gen ( i_strb, 4, MMAX_HALF );
            end
            'd8: begin
                lane_1_valid = output_valid_gen ( i_strb, 8, MMAX_HALF );
            end
        endcase
    
    end 
end


//
// BLK WIDTH CALCULATION
//

assign blk_wdth_0 = 1 << (cmd_m_0 + 1 + cmd_os_0 - cmd_l_0); // The extra 1 is for dual rail
assign blk_wdth_1 = 1 << (cmd_m_1 + 1 + cmd_os_1 - cmd_l_1);

always_ff@ (posedge clk) begin
    for (int i = 0; i < LMAX_HALF; i++ ) begin: BLK_WIDTH_LANE_0_to_3
        o_blk_bit_width[i] <= blk_wdth_0;
    end

    for (int i = LMAX_HALF; i < LMAX; i++ ) begin: BLK_WIDTH_LANE_4_to_7
        o_blk_bit_width[i] <= cmd_mode ? blk_wdth_1 : blk_wdth_0;
    end
end


//
// LOGIC THAT WILL PACK SAMPLES INTO 1-D ARRAY 
//

always_ff @(posedge clk) begin
    int_buf_d <= int_buf;
end

always_comb begin 
    int_buf = '0;

    if ( cmd_mode == 0 ) begin // Single mode case and only cmd_np_0 and cmd_os_0 take effect

        case ( cmd_np_0 ) 
            12 : begin 
                int_buf = sample_mapping_sm ( i_lag_r0, i_lag_r1, cmd_os_0, 12 );
            end

            16 : begin 
                int_buf = sample_mapping_sm ( i_lag_r0, i_lag_r1, cmd_os_0, 16 );
            end

            24 : begin
                int_buf = sample_mapping_sm ( i_lag_r0, i_lag_r1, cmd_os_0, 24 );
            end

            32 : begin 
                int_buf = sample_mapping_sm ( i_lag_r0, i_lag_r1, cmd_os_0, 32 );
            end

            48 : begin
                int_buf = sample_mapping_sm ( i_lag_r0, i_lag_r1, cmd_os_0, 48 );
            end

        endcase
    
    end else begin // This is the dual mode case.


        case ( cmd_np_0 ) 
            12 : begin
                case ( cmd_np_1) 
                    12 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 12, 12);
                    end

                    16 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 12, 16);
                    end

                    24 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 12, 24);
                    end

                    32 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 12, 32);
                    end

                    48 : begin
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 12, 48);
                    end
                endcase
            end

            16 : begin 
                case ( cmd_np_1) 
                    12 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 16, 12);
                    end

                    16 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 16, 16);
                    end

                    24 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 16, 24);
                    end

                    32 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 16, 32);
                    end

                    48 : begin
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 16, 48);
                    end
                endcase
            end

            24 : begin
                case ( cmd_np_1) 
                    12 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 24, 12);
                    end

                    16 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 24, 16);
                    end

                    24 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 24, 24);
                    end

                    32 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 24, 32);
                    end

                    48 : begin
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 24, 48);
                    end
                endcase
            end

            32 : begin 
                case ( cmd_np_1) 
                    12 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 32, 12);
                    end

                    16 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 32, 16);
                    end

                    24 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 32, 24);
                    end

                    32 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 32, 32);
                    end

                    48 : begin
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 32, 48);
                    end
                endcase
            end

            48 : begin
                case ( cmd_np_1) 
                    12 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 48, 12);
                    end

                    16 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 48, 16);
                    end

                    24 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 48, 24);
                    end

                    32 : begin 
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 48, 32);
                    end

                    48 : begin
                        int_buf = sample_mapping_dm ( i_lag_r0, i_lag_r1, cmd_os_0, cmd_os_1, 48, 48);
                    end
                endcase
            end

        endcase
    end // End mode if-else
end // End always_comb


//
// LOGIC THAT SPLITS 1-D ARRAY TO DIFFERENT LANES
//
// In this peice of logic, given the samples have been
// coagulated into a 1D array, we now want to split it to
// each lane

always_comb begin
    
    // Initialize to zero
    for (int i=0; l<LMAX; l++) begin
        lane_data[l] = {LSAMP_W{1'b0}};
    end

    // Based on link mode slice data out of int_buf and assign it
    // to lane_data for all lanes. 

    if ( cmd_mode == 0 ) begin // Single Link case
        case (blk_wdth_0_d)
            'd16 : begin
                lane_data = lane_mapping_sm ( int_buf, LMAX, 16, 0 );
            end

            'd24 : begin
                lane_data = lane_mapping_sm ( int_buf, LMAX, 24, 0 );
            end

            'd32 : begin
                lane_data = lane_mapping_sm ( int_buf, LMAX, 32, 0 );
            end

            'd48 : begin
                lane_data = lane_mapping_sm ( int_buf, LMAX, 48, 0 );
            end

            'd64 : begin
                lane_data = lane_mapping_sm ( int_buf, LMAX, 64, 0 );
            end

            'd96 : begin
                lane_data = lane_mapping_sm ( int_buf, LMAX, 96, 0 );
            end

            'd128 : begin
                lane_data = lane_mapping_sm ( int_buf, LMAX, 128, 0 );
            end

            'd192 : begin
                lane_data = lane_mapping_sm ( int_buf, LMAX, 192, 0 );
            end

            'd256 : begin
                lane_data = lane_mapping_sm ( int_buf, LMAX, 256, 0 );
            end

            'd384 : begin
                lane_data = lane_mapping_sm ( int_buf, LMAX, 384, 0 );
            end

            'd512 : begin // With 512 the max you can do is 4 lanes. See JESD_RATES excel sheet.
                lane_data[LMAX_HALF-1 : 0] = lane_mapping_sm ( int_buf, LMAX_HALF, 512, 0 );
            end
        endcase
    end else begin //Dual Link Case
        offset = MMAX * (1 << cmd_os_0) * cmd_np_0;

        case (blk_wdth_0_d)
            'd16 : begin
                lane_data[LMAX_HALF-1:0] = lane_mapping_dm ( int_buf, LMAX_HALF, 16, 0 );
            end

            'd24 : begin
                lane_data[LMAX_HALF-1:0] = lane_mapping_dm ( int_buf, LMAX_HALF, 24, 0 );
            end

            'd32 : begin
                lane_data[LMAX_HALF-1:0] = lane_mapping_dm ( int_buf, LMAX_HALF, 32, 0 );
            end

            'd48 : begin
                lane_data[LMAX_HALF-1:0] = lane_mapping_dm ( int_buf, LMAX_HALF, 48, 0 );
            end

            'd64 : begin
                lane_data[LMAX_HALF-1:0] = lane_mapping_dm ( int_buf, LMAX_HALF, 64, 0 );
            end

            'd96 : begin
                lane_data[LMAX_HALF-1:0] = lane_mapping_dm ( int_buf, LMAX_HALF, 96, 0 );
            end

            'd128 : begin
                lane_data[LMAX_HALF-1:0] = lane_mapping_dm ( int_buf, LMAX_HALF, 128, 0 );
            end

            'd192 : begin
                lane_data[LMAX_HALF-1:0] = lane_mapping_dm ( int_buf, LMAX_HALF, 192, 0 );
            end

            'd256 : begin
                lane_data[LMAX_HALF-1:0] = lane_mapping_dm ( int_buf, LMAX_HALF, 256, 0 );
            end

            'd384 : begin
                lane_data[LMAX_HALF-1:0] = lane_mapping_dm ( int_buf, LMAX_HALF, 384, 0 );
            end

            'd512 : begin // With 512 the max you can do is 4 lanes. See JESD_RATES excel sheet.
                lane_data[LMAX_HALF-1:0] = lane_mapping_dm ( int_buf, LMAX_HALF, 512, 0 );
            end
        endcase

        case (blk_wdth_1_d)
            'd16 : begin
                lane_data[LMAX-1:LMAX_HALF] = lane_mapping_dm ( int_buf, LMAX_HALF, 16, offset );
            end

            'd24 : begin
                lane_data[LMAX-1:LMAX_HALF] = lane_mapping_dm ( int_buf, LMAX_HALF, 24, offset );
            end

            'd32 : begin
                lane_data[LMAX-1:LMAX_HALF] = lane_mapping_dm ( int_buf, LMAX_HALF, 32, offset );
            end

            'd48 : begin
                lane_data[LMAX-1:LMAX_HALF] = lane_mapping_dm ( int_buf, LMAX_HALF, 48, offset );
            end

            'd64 : begin 
                lane_data[LMAX-1:LMAX_HALF] = lane_mapping_dm ( int_buf, LMAX_HALF, 64, offset );
            end

            'd96 : begin
                lane_data[LMAX-1:LMAX_HALF] = lane_mapping_dm ( int_buf, LMAX_HALF, 96, offset );
            end

            'd128 : begin
                lane_data[LMAX-1:LMAX_HALF] = lane_mapping_dm ( int_buf, LMAX_HALF, 128, offset );
            end

            'd192 : begin
                lane_data[LMAX-1:LMAX_HALF] = lane_mapping_dm ( int_buf, LMAX_HALF, 192, offset );
            end

            'd256 : begin
                lane_data[LMAX-1:LMAX_HALF] = lane_mapping_dm ( int_buf, LMAX_HALF, 256, offset );
            end

            'd384 : begin 
                lane_data[LMAX-1:LMAX_HALF] = lane_mapping_dm ( int_buf, LMAX_HALF, 384, offset );
            end

            'd512 : begin // With 512 the max you can do is 4 lanes. See JESD_RATES excel sheet.
                lane_data[LMAX-1:LMAX_HALF] = lane_mapping_dm ( int_buf, LMAX_HALF, 512, offset );
            end
        endcase

    end 
end

/* 
 * Function: output_valid
 * Parameters:
     * i_strb: The input strobes of all 16 converters
     * num_m : Number of converters to consider
     * offset: Offset from which to consider num_m converters
 * 
 * Description:
 * The function is used to set the o_valid of a lane. By design, converters
 * within a link will have the same sampling rate and hence strobe pattern. 
 * The same output valid can be routed to the concerned number of lanes. 
 */

function logic output_valid_gen ( logic [MMAX - 1 : 1] i_strb, int num_m, int offset ) begin
    logic o_valid = 0;

    for ( int m = offset; m < offset + num_m; m++ ) begin 
        o_valid |= i_strb[m];
    end

    return o_valid;

end


function logic [ LMAX - 1 : 0 ] o_valid_sm_set ( logic valid, int num_lane ) begin

    logic [ LMAX - 1 : 0 ] o_valid = '0;

    for ( int l = 0; l < num_lane ; l++ ) begin
        o_valid[l] = lane_0_valid;
    end
    for ( int l = 1; l < LMAX; l++ ) begin
        o_valid[l] = 0;
    end

    return o_valid;

end

function logic [ LMAX_HALF - 1 : 0 ] o_valid_dm_set ( logic valid, int num_lane ) begin

    logic [ LMAX_HALF - 1 : 0 ] o_valid = '0;

    for ( int l = 0; l < num_lane ; l++ ) begin
        o_valid[l] = lane_0_valid;
    end
    for ( int l = 1; l < LMAX_HALF; l++ ) begin
        o_valid[l] = 0;
    end

    return o_valid;

end


/*
 * Function: sample_mapping_sm
 * Parameters:
     * c0 : This is the first rail coming from CWSWP block
     * c1 : This is the second rail coming from CWSP block
     * os : Whether oversampling is set or not
     * np : The np setting
     *
 * Description:
 * In this function samples from the two rails are packed into the internal 1D 
 * buffer. Oversampling dictates if a sample is replicated and concatenated. 
 * 
 */ 

function buf_t sample_mapping_sm ( cswp_t c0, cswp_t c1, logic os, logic [6:0] np) begin 

    // The size of this internal buffer is set to 
    // M x Number of Rails x Max NP
    buf_t int_buf = '0;

    // The offset is used to pack the second
    // rail. This will generate an offset for each case
    // where we call this function. Maybe better to bring
    // this out and feed it as an input this way we can reduce
    // the number of multipliers. 
    int offset = MMAX * ( 1 << os ) * np;

    if ( os == 0) begin // No oversampling case
        for ( int m = 0; m < MMAX; m++ ) begin
            int_buf = int_buf | c0[m] << (m * np);
            int_buf = int_buf | c1[m] << (offset + m * np);
        end
    end else begin
        for ( int m = 0; m < 2*MMAX; m=m+2 ) begin
            int_buf = int_buf | c0[m] << (m * np);
            int_buf = int_buf | c0[m] << (( m + 1 ) * np);
            int_buf = int_buf | c1[m] << (offset + m * np);
            int_buf = int_buf | c1[m] << (offset + ( m + 1 ) * np);
        end
    end 

    return int_buf; 

endfunction : sample_mapping_sm


/*
 * Function: sample_mapping_dm
 * Parameters:
     * c0 : This is the first rail coming from CWSWP block
     * c1 : This is the second rail coming from CWSP block
     * os_0 : Whether oversampling is set or not for link 0
     * os_1 : Whether oversampling is set or not for link 1
     * np_0 : The np setting for link 0
     * np_1 : The np setting for link 1
 * Description:
 * In this function samples from the two rails are packed into the internal 1D 
 * buffer. In the dual mode case each rail is considered a separate link. 
 * Oversampling dictates if a sample is replicated and concatenated. 
 * 
 */ 

function buf_t sample_mapping_dm ( cswp_t c0, cswp_t c1, logic os_0, logic os_1, logic [6:0] np_0, logic [6:0] np_1) begin
    buf_t int_buf = '0;

    int offset = MMAX * ( 1 << os_0) * np_0;

    if ( os_0 == 0) begin // No oversampling case
        for ( int m = 0; m < MMAX; m++ ) begin
            int_buf = int_buf | c0[m] << (m * np_0);
        end
    end else begin
        for ( int m = 0; m < 2*MMAX; m=m+2 ) begin
            int_buf = int_buf | c0[m] << (m * np);
            int_buf = int_buf | c0[m] << (( m + 1 ) * np);
        end
    end 

    
    if ( os_1 == 0) begin // No oversampling case
        for ( int m = 0; m < MMAX; m++ ) begin
            int_buf = int_buf | c1[m] << (offset + m * np_1);
        end
    end else begin
        for ( int m = 0; m < 2*MMAX; m=m+2 ) begin
            int_buf = int_buf | c1[m] << (offset + m * np_1);
            int_buf = int_buf | c1[m] << (offset + ( m + 1 ) * np_1);
        end
    end 

    return int_buf; 
endfunction : sample_mapping_dm



function lasmph_t lane_mapping_dm ( buf_t int_buf, int num_lane, int jump, int offset ) begin

    lsamph_t lsamp;

    for (int l = 0; l < num_lane; l ++) begin
        lsamp[l] = {(512-jump){1'b0}, int_buf[offset + l*jump +: jump]; 
    end

    return lsamp;

endfunction

function lasmp_t lane_mapping_sm ( buf_t int_buf, int num_lane, int jump, int offset ) begin

    lsamp_t lsamp;

    for (int l = 0; l < num_lane; l ++) begin
        lsamp[l] = {(512-jump){1'b0}, int_buf[offset + l*jump +: jump]; 
    end

    return lsamp;

endfunction
