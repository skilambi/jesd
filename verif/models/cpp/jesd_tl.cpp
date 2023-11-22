#include <iostream>
#include <iomanip>
using namespace std;

class JesdTl {
    public:
        // Members
        uint32_t M; // Number of Real Converters
        uint32_t L; // Number of Lanes
        uint32_t Np; // JESD TL Precision
        uint32_t R; // Rate of the input

        int num_samples; // This is the number of samples that this block will process
                         // Allows us to define internal data structures of the right size.
                         // In real hardware this would just be a streaming block.
        
        uint64_t** ng_data;     // This is a 2D array that will store converter raw samples to word mapping.
                                // We define this as 64 bit so that we can accomodate max 48 bit support.
                                // First dimension (Rows) is the number of converters and the second 
                                // dimension is the number of samples we are processing.
        
        uint16_t** ng_valid;     // This is a 2D array that marks which samples are valid. 1 for valid, 0 for in
                                // valid. 
        
        uint64_t** lane_out;    // 2-D array that will store the lane outputs. First dimension is the number of lanes
                                // and second dimension is the number of samples. 
        uint16_t** lane_valid;   // valid for lane output

        // Constructors
        JesdTl () {
            setL(2);
            setM(2);
            setNp(16);
            setR(1);
            setNumSamp(16);
            
            // Nibble group array.
            ng_data = new uint64_t*[getM()];
            for ( int i = 0; i < getM(); i++) {
                ng_data[i] = new uint64_t[num_samples];
            } 

            // Nibble group valids.
            ng_valid = new uint16_t*[getM()];
            for ( int i = 0; i < getM(); i++) {
                ng_valid[i] = new uint16_t[num_samples];
            } 

            // Lane output arrays.
            lane_out = new uint64_t*[getL()];
            for ( int i = 0; i < getL(); i++) {
                lane_out[i] = new uint64_t[num_samples];
            } 

            // Lane output valids.
            lane_valid = new uint16_t*[getL()];
            for ( int i = 0; i < getL(); i++) {
                lane_valid[i] = new uint16_t[num_samples];
            } 

        
        }

        JesdTl ( uint32_t L, uint32_t M, uint32_t Np, uint32_t R, int num_samples) {
            setL ( L );
            setM ( M );
            setNp ( Np );
            setR ( R );
            setNumSamp ( num_samples );

            // Create a 2-D array for converter raw word to word mapping
            ng_data = new uint64_t*[getM()];
            for ( int i = 0; i < getM(); i++) {
                ng_data[i] = new uint64_t[num_samples];
            } 

            // Create a 2-D array for valids
            ng_valid = new uint16_t*[getM()];
            for ( int i = 0; i < getM(); i++) {
                ng_valid[i] = new uint16_t[num_samples];
            }

            init_ng();  

            // Lane output arrays.
            lane_out = new uint64_t*[getL()];
            for ( int i = 0; i < getL(); i++) {
                lane_out[i] = new uint64_t[num_samples];
            } 

            // Lane output valids.
            lane_valid = new uint16_t*[getL()];
            for ( int i = 0; i < getL(); i++) {
                lane_valid[i] = new uint16_t[num_samples];
            }

            init_lane_output();  
        }

        // Getter and Setter Methods
        void setR ( uint32_t R ) {
            this->R = R;
            setP();
        }

        void setM ( uint32_t M ) {
            uint32_t allowed_M[] = { 2, 4, 8, 16 };

            int n = sizeof(allowed_M)/sizeof(allowed_M[0]);

            for ( int i = 0 ; i < n ; i++) {
                if ( allowed_M[i] == M ) {
                    this->M = M;
                    return;
                }
            }
            //throw 
        }

        void setL ( uint32_t L ) { 
            this->L = L;
        }

        void setNp ( uint32_t Np ) { 
            this->Np = Np;
        }

        void setNumSamp ( int num_samples ) { 
            this->num_samples = num_samples;
        }
        
        uint32_t getM ( ) { 
            return M * P;
        }

        uint32_t getL ( ) { 
            return L;
        }

        uint32_t getNp ( ) { 
            return Np;
        }

        uint32_t getR ( ) {
            return R;
        }

        // Init methods
        /*
            Function: init_lane_output
            Description:
            The purpose of this function is initialize the internal lane output
            array
         */
        void init_lane_output() {
            for ( int r = 0 ; r < getL() ; r ++ ) {
                for ( int c = 0 ; c < num_samples ; c ++ ) {
                    lane_out[r][c]      = 0;
                    lane_valid[r][c]    = 0;
                }
            }
        }

        /*
            Function: init_ng
            Description:
            The purpose of this function is initialize the internal ng_data array
            array
         */
        void init_ng() {
            for ( int r = 0 ; r < getM() ; r ++ ) {
                for ( int c = 0 ; c < num_samples ; c ++ ) {
                    ng_data[r][c]      = 0;
                    ng_valid[r][c]     = 0;
                }
            }
        }

        // Logic Methods

        /*  
            Function: map_cw_2_ng
            Description:
            The purpose of this function is convert convertor words (which are the raw converter samples) to nibble groups (ng)
            as described in Fig 38 of the JESD204C document. Convertor words can be either 12 bits or 16 bits. These
            can be mapped to ng that are of size 12, 16, 24, 32 or 48. So the purpose of this function is to expand
            the raw samples to nibble group depending on the Np setting of this class. 
            Arguments: 
            raw_conv_data: 2D array where the number of rows is the number of converters times phases and columns is
                number of samples (valid or invalid). Note that raw converter samples can either be 12 bit or 16 bit.
                However the datatype for raw_conv_data is uint16_t. So the assumption here is for the 12 bit case, the
                sample will be MSB alligned meaning, the last 4 LSBs will just be 0.
            valid: This 2D data provides a valid array for every converter (and its phase). This is just to make processing
                easier 
        */
        void map_cw_2_ng ( uint16_t** raw_conv_data, uint16_t** valid ) {
            int num_row = M * P;

            for ( int r = 0; r < num_row; r ++ ) {
                for ( int c = 0; c < num_samples; c ++) {
                    ng_valid[r][c] = valid[r][c];
                    switch ( Np ) {
                        case 12: {
                            ng_data[r][c] =  ( (uint64_t) raw_conv_data[r][c] ) >> 4;
                            break;
                        }
                        case 16: {
                            ng_data[r][c] =  ( (uint64_t) raw_conv_data[r][c] );
                            break;
                        }
                        case 24: {
                            ng_data[r][c] =  ( (uint64_t) raw_conv_data[r][c] ) << 8;
                            break;   
                        }
                        case 32: {
                            ng_data[r][c] =  ( (uint64_t) raw_conv_data[r][c] ) << 16;
                            break;   
                        }
                        case 48: {
                            ng_data[r][c] = ( (uint64_t) raw_conv_data[r][c] ) << 32;
                            break;   
                        }
                    }
                }
            }

            // The following is just for debug. Comment out when not needed
            // Now print all the samples 
            
            for ( int m = 0; m < num_row; m ++ ) {
                for ( int s = 0; s < num_samples; s ++ ) {
                    cout << hex  << setw(16) << ng_data[m][s] << " ";
                }
                cout << endl;
            } 

            for ( int m = 0; m < num_row; m ++ ) {
                for ( int s = 0; s < num_samples; s ++ ) {
                    cout << hex  << setw(16) << ng_valid[m][s] << " ";
                }
                cout << endl;
            }  

        }  

        /*
         */

        void map_ng_2_lane_v1 ( ) {
            // Split (M x P) number of converters across L lanes. We will call these blocks. In a valid
            // input cycle, blk_bit_width number of bits will be fed into the lane word. If blk_bit_width
            // is <= 64, it will get accrued inside of the lane word. When we have 64 bits ready to send
            // we will send it out. When blk_bit_width > 64, we may need to send more than one 64 bit word
            // back to back. This is a little tricky but you can use a dead cycle to do this.  
            int blk_size = (M * P) / L;
            int blk_bit_width = blk_size * Np;
            cout << dec << "Blk Size: " << blk_size << ", Blk Bit Width: " << blk_bit_width << endl;

            // Lets define lane input sample whose size is dependent on M x P split accross L. 
            // The maxium we know will ever be 256 bits. 
            uint64_t lane_input_sample[L][4];
            // Lane input bit counter. Bit counter that keeps track of 
            // how many bits have been stored in.
            int in_bit_cntr = 0;
            // This variable is used for figuring out which 64 bit word needs
            // to get the data.
            int samp_col = 0;

            // These buffers store the 64 bit word that needs to be transmitted.
            uint64_t lane_buf_pg0[L];
            uint64_t lane_buf_pg1[L];
            // Keeps track of accumulated number of bits for a lane.
            uint16_t lane_bit_cntr[L];
            bool page[L];

            // Initialize the buffers
            for (int l = 0 ; l < L ; l ++) {
                lane_buf_pg0[l] = 0;
                lane_buf_pg1[l] = 0;
                lane_bit_cntr[l] = 0;
                page[l] = false;

                for ( int s = 0; s < 4; s ++ ) {
                    lane_input_sample[l][s] = 0;
                } 
            }

            // Iterate over every sample in ng_data.
            for ( int s = 0; s < num_samples; s ++ ) {
                // Iterate through every lane and collect the data that belongs to that lane
                for ( int l = 0; l < L; l ++ ) {
                    // Iterate through the rows (converters) in each block and collect the
                    // the data that belongs to that lane in lane_input_sample. Note in hw
                    // this will be a case statement on blk_bit_width, where we assign the right
                    // samples from converters to a lane.
                    for ( int r = l * blk_size; r < (l + 1)*blk_size ; r ++ ) {
                        
                        if ( ng_valid[r][s] == 1) {
                            samp_col = lane_bit_cntr[l] / 64;
                            int shift_bits = (lane_bit_cntr[l] % 64);
                            lane_input_sample[l][samp_col] |= (ng_data[r][s] << shift_bits );
                            // If shift_bits + Np > 64 then a part of the ng_data needs to be buffered
                            // into the next column index. For instance if Np = 12 and blk_bit_width
                            // is 96 bits, i.e., 96 bits need to flow into a lane, then the last 8 bits
                            // should go into the next column
                            if ( shift_bits + Np > 64) {
                               lane_input_sample[l][samp_col+1] |= ng_data[r][s] >> (64 - shift_bits); 
                            }
                            lane_bit_cntr[l] += Np;
                        }
                    }

                    // Debug
                    cout << dec << "Sample: " << s << " Lane " << l << ": " << hex << setw(16) << lane_input_sample[l][3] << hex << setw(16) << lane_input_sample[l][2] << 
                    hex << setw(16) << lane_input_sample[l][1] << hex << setw(16) << lane_input_sample[l][0] << " ---> " << dec << lane_bit_cntr[l] << endl;
                    
                    if (lane_bit_cntr[l] >= 64) {
                        lane_out[l][s] = arr_pop(lane_input_sample[l], 4);
                        lane_valid[l][s] = 1;
                        lane_bit_cntr[l] -= 64;
                    } else {
                        lane_out[l][s] = 0;
                        lane_valid[l][s] = 0;
                    }

                
                } // end l-for


            } // End s-for


        } // end function
        
        void map_ng_2_lane ( ) {
            // Split (M x P) number of converters across L lanes. We will call these blocks. In a valid
            // input cycle, blk_bit_width number of bits will be fed into the lane word. If blk_bit_width
            // is <= 64, it will get accrued inside of the lane word. When we have 64 bits ready to send
            // we will send it out. When blk_bit_width > 64, we may need to send more than one 64 bit word
            // back to back. This is a little tricky but you can use a dead cycle to do this.  
            int blk_size = (M * P) / L;
            int blk_bit_width = blk_size * Np;
            cout << dec << "Blk Size: " << blk_size << ", Blk Bit Width: " << blk_bit_width << endl;

            // Lets define lane input sample whose size is dependent on M x P split accross L. 
            // The maxium we know will ever be 256 bits. 
            uint64_t lane_input_sample[L][4];
            // Lane input bit counter. Bit counter that keeps track of 
            // how many bits have been stored in.
            int in_bit_cntr = 0;
            // This variable is used for figuring out which 64 bit word needs
            // to get the data.
            int samp_col = 0;

            // These buffers store the 64 bit word that needs to be transmitted.
            uint64_t lane_buf_pg0[L];
            uint64_t lane_buf_pg1[L];
            // Keeps track of accumulated number of bits for a lane.
            uint16_t lane_bit_cntr[L];
            bool page[L];

            // Initialize the buffers
            for (int i = 0 ; i < L ; i ++) {
                lane_buf_pg0[i] = 0;
                lane_buf_pg1[i] = 0;
                lane_bit_cntr[i] = 0;
                page[i] = false;
            }

            // Iterate over every sample in ng_data.
            for ( int s = 0; s < num_samples; s ++ ) {
                // First initialize the lane_inpu_sample for each sample. This is
                // needed because think it as a brand new sample each iteration
                for (int l = 0; l < L; l++) {
                    for ( int k = 0; k < 4; k ++ ) {
                        lane_input_sample[l][k] = 0;
                    }
                }

                // Iterate through every lane and collect the data that belongs to that lane
                for ( int l = 0; l < L; l ++ ) {
                    // Iterate through the rows (converters) in each block and collect the
                    // the data that belongs to that lane in lane_input_sample. Note in hw
                    // this will be a case statement on blk_bit_width, where we assign the right
                    // samples from converters to a lane.
                    in_bit_cntr = 0;
                    for ( int r = l * blk_size; r < (l + 1)*blk_size ; r ++ ) {
                        
                        if ( ng_valid[r][s] == 1) {
                            samp_col = in_bit_cntr / 64;
                            int shift_bits = (in_bit_cntr % 64);
                            lane_input_sample[l][samp_col] |= (ng_data[r][s] << shift_bits );
                            // If shift_bits + Np > 64 then a part of the ng_data needs to be buffered
                            // into the next column index. For instance if Np = 12 and blk_bit_width
                            // is 96 bits, i.e., 96 bits need to flow into a lane, then the last 8 bits
                            // should go into the next column
                            if ( shift_bits + Np > 64) {
                               lane_input_sample[l][samp_col+1] |= ng_data[r][s] >> (64 - shift_bits); 
                            }
                            in_bit_cntr += Np;
                        }  
                    }

                    // Debug
                    cout << dec << "Sample: " << s << " Lane " << l << ": " << hex << setw(16) << lane_input_sample[l][2] << 
                    hex << setw(16) << lane_input_sample[l][1] << hex << setw(16) << lane_input_sample[l][0] << endl;
                
                    // At this point you have collected the converter sample data into lane_input_sample
                    // You now want to feed into the lane. This is where things get tricky. First thing to note
                    // is we can use one of the ng valids as the input valid for each lane. We will need a case statement
                    // on blk_bit_width.

                    
                    if ( ng_valid[l*blk_size][s] == 1 ) { //following updates should be done only during a valid sample

                        switch ( blk_bit_width ) {
                            case 16: case 24: case 32: case 48: case 64: case 96: case 128: {

                                if ( !page[l] ) { // we are page 0

                                    lane_buf_pg0[l] |= lane_input_sample[l][0] << lane_bit_cntr[l]; 
                                    // Check to see if something needs to be stored in page 1 when
                                    // shifting in the current sample.
                                    if ( lane_bit_cntr[l] + blk_bit_width > 64 ) {
                                        if ((blk_bit_width == 96) || (blk_bit_width == 128)) {
                                            // only two cases, either we have a 32 bit remnant 
                                            // from previous iteration or we are starting a new
                                            // 96 bit cycle. 
                                            if ( lane_bit_cntr[l] == 0) {
                                                lane_buf_pg1[l] |= lane_input_sample[l][1]; 
                                            } else { // 32 bit case
                                                lane_buf_pg1[l] |= lane_input_sample[l][0] >> 32;
                                                lane_buf_pg1[l] |= lane_input_sample[l][1] << 32;
                                            }
                                        } else {
                                            lane_buf_pg1[l] |= lane_input_sample[l][0] >> (64 - lane_bit_cntr[l]); 
                                        }
                                    }

                                    // Increment lane bit counter
                                    lane_bit_cntr[l] += blk_bit_width;

                                    // Check to see if buffer has complete data to send
                                    if ( lane_bit_cntr[l] >= 64 ) {
                                        lane_out[l][s] = lane_buf_pg0[l];
                                        lane_valid[l][s] = 1;

                                        // Reset lane buffer for next time
                                        lane_buf_pg0[l] = 0;
                                        page[l] = true;

                                        // Update the counter correctly
                                        lane_bit_cntr[l] -= 64;
                                    } else {
                                        lane_out[l][s] = lane_buf_pg0[l];
                                        lane_valid[l][s] = 0;
                                    }   

                                } else { // we are in page 1

                                   lane_buf_pg1[l] |= lane_input_sample[l][0] << lane_bit_cntr[l]; 
                                    // Check to see if something needs to be stored in page 1 when
                                    // shifting in the current sample.
                                    if ( lane_bit_cntr[l] + blk_bit_width > 64 ) {
                                        if ((blk_bit_width == 96) || (blk_bit_width == 128)){
                                            // only two cases, either we have a 32 bit remnant 
                                            // from previous iteration or we are starting a new
                                            // 96 bit cycle. 
                                            if ( lane_bit_cntr[l] == 0) {
                                                lane_buf_pg0[l] |= lane_input_sample[l][1]; 
                                            } else { // 32 bit case
                                                lane_buf_pg0[l] |= lane_input_sample[l][0] >> 32;
                                                lane_buf_pg0[l] |= lane_input_sample[l][1] << 32;
                                            }
                                        }
                                        else { 
                                            lane_buf_pg0[l] |= lane_input_sample[l][0] >> (64 - lane_bit_cntr[l]); 
                                        }
                                    }

                                    // Increment lane bit counter
                                    lane_bit_cntr[l] += blk_bit_width;

                                    // Check to see if buffer has complete data to send
                                    if ( lane_bit_cntr[l] >= 64 ) {
                                        lane_out[l][s] = lane_buf_pg1[l];
                                        lane_valid[l][s] = 1;

                                        // Reset lane buffer for next time
                                        lane_buf_pg1[l] = 0;
                                        page[l] = false;

                                        // Update the counter correctly
                                        lane_bit_cntr[l] -= 64;
                                    } else {
                                        lane_out[l][s] = lane_buf_pg1[l];
                                        lane_valid[l][s] = 0;
                                    }  

                                }

                                break;
                            }
                        }
                    } else { // if its not a valid cycle then just copy over previous sample (register wont be updated)
                        if ( lane_bit_cntr[l] >=64 ) {
                            if ( !page[l] ) {
                               lane_out[l][s] = lane_buf_pg0[l];
                               lane_buf_pg0[l] = 0; 
                               page[l] = true; 
                            } else {
                               lane_out[l][s] = lane_buf_pg1[l];
                               lane_buf_pg1[l] = 0;
                               page[l] = false;  
                            }
                            lane_valid[l][s] = 1;
                            lane_bit_cntr[l] -= 64;
                        } else { 
                            lane_out[l][s] = lane_out[l][s-1];
                            lane_valid[l][s] = 0;
                        } 
                    }

                }


            }


        }

    private:
        uint32_t P; // Number of phases

        void setP() {
            //P will be set based on R
            if (this->R > 4)
                this->P = 2;
            else
                this->P = 1;
        }

        /*
            Function: arr_pop
            Parameters:
                arr: A 1D array
                len: Length of the arra
            Description:
                The function mimics FIFO in that it will pop
                out the top 64 bit number and shift all other members
                up by one. In HW this is mimicing logical right shift by 64.
         */
        uint64_t arr_pop (uint64_t* arr, int len) {
            uint64_t temp;
            temp = arr[0];

            for (int i=1; i<len; i++) {
                arr[i-1] = arr[i];
            }
            arr[len-1] = 0;
            return temp;
        }




};

/* ==========================================================
            EXTERNAL FUNCTIONS (not part of class methods)
   ==========================================================    */

void adj_input_data_dim(uint32_t* col, uint16_t R, int num_samp){
    // Depending on the Rate we want to insert dummy values
    // that are not valid samples. Hence we need to define a new
    // number of samples.
    uint32_t mod_num_samp;

    switch ( R ){
        case 1: { // 122.88 MSps
            mod_num_samp = num_samp * 4;
            break;
        }
        case 2: { // 245.76 MSps
            mod_num_samp = num_samp * 2;
            break;
        }
        case 3: { // 368.64 MSps
            mod_num_samp = (4/3) * num_samp;
            break;
        }
        case 4: { // 491.52 MSps
            mod_num_samp = num_samp;
            break;
        }
        case 6: {
            mod_num_samp = (4/3) * num_samp;
            break;
        }
        case 8: { // 491.52 MSps
            mod_num_samp = num_samp;
            break;
        } 
    }
    *col = mod_num_samp;
}

void gen_conv_data(uint16_t** inp_data, uint16_t** valid, int row, int col, int R) {

    // Now initialize the input data with random values
    for ( int m = 0; m < row; m ++ ) {
        for ( int s = 0; s < col; s ++ ) {
            //Based on the rate we put samples only in
            //needed locations
            switch ( R ) {
                case 1: { // 122.88 MSps
                    if(s%4 == 0) {
                        inp_data[m][s] = rand();
                        valid[m][s] = 1;
                    }else{ 
                        inp_data[m][s] = 0;
                        valid[m][s] = 0;
                    }
                    break; 
                }

                case 2: { // 
                    if(s%2 == 0) {
                        inp_data[m][s] = rand();
                        valid[m][s] = 1;
                    } else { 
                        inp_data[m][s] = 0;
                        valid[m][s] = 0; 
                    }
                    break;
                }

                case 3: case 6: {
                    if(s%4 == 0 || s%4 == 1 || s%4 == 2) { 
                        inp_data[m][s] = rand();
                        valid[m][s] = 1;
                    } else {  
                        inp_data[m][s] = 0;
                        valid[m][s] = 0;
                    } 
                    break;
                }

                case 4: case 8: {
                    inp_data[m][s] = rand();
                    valid[m][s] = (uint8_t) 1;
                    break;
                }

            }
        }
    }
}

int main(int argc, char *argv[]) {
    // Number of Lanes
    uint32_t L = 2;
    // Number of real converters
    uint32_t M = 16;
    // Precision
    uint32_t Np = 24;
    // Rate
    uint32_t R = 1;
    // Number of samples
    uint32_t num_samp = 12;


    // We will now prepare the input data. In the model
    // the number of rows will be the number of converters
    // we are defining. The number of columns will be the
    // number of samples. However note the number of samples
    // will need to be adjusted based on the rate
    uint32_t adj_num_samp ;
    // Adjust the number of input samples based on rate
    adj_input_data_dim(&adj_num_samp, R, num_samp);

    // Create the JESDTL object. Need to create this
    // before the inp_data array creation.
    JesdTl tlobj(L, M, Np, R, adj_num_samp);


    // Now create a 2-D array where the rows are converters
    // and the columns are input samples for each converter.
    uint16_t** inp_data;
    inp_data = new uint16_t*[tlobj.getM()];

    for ( int i = 0; i < tlobj.getM(); i++) {
        inp_data[i] = new uint16_t[adj_num_samp];
    }

    uint16_t** valid;
    valid = new uint16_t*[tlobj.getM()];

    for ( int i = 0; i < tlobj.getM(); i++) {
        valid[i] = new uint16_t[adj_num_samp];
    }


    // Generate random input data
    gen_conv_data ( inp_data, valid, tlobj.getM(), adj_num_samp, tlobj.getR());

    // Print this input array for debug.
    cout << internal << setfill('0');
    // Now print all the samples 
    for ( int m = 0; m < tlobj.getM(); m ++ ) {
        for ( int s = 0; s < adj_num_samp; s ++ ) {
            cout << hex  << setw(6) << inp_data[m][s] << " ";
        }
        cout << endl;
        for ( int s = 0; s < adj_num_samp; s ++ ) {
            cout << valid[m][s] << " ";
        }
        cout << endl;
    }

    tlobj.map_cw_2_ng(inp_data, valid);
    tlobj.map_ng_2_lane_v1( );

    for ( int r = 0 ; r < tlobj.getL(); r ++) {
        for ( int c = 0 ; c < adj_num_samp ; c ++) {
            cout << hex  << setw(16) << tlobj.lane_out[r][c] << " ";
        }
        cout << endl;
        for ( int c = 0 ; c < adj_num_samp ; c ++) {
            cout << hex  << setw(16) << tlobj.lane_valid[r][c] << " ";
        }
        cout << endl;
    } 

    free(inp_data);
    free(valid);
    return 0;
}
