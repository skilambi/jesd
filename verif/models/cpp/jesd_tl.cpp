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
        
        uint64_t** ng_data;   // This is a 2D array that will store converter raw samples to word mapping.
                                // We define this as 64 bit so that we can accomodate max 48 bit support.

        // Constructors
        JesdTl () {
            setL(2);
            setM(2);
            setNp(16);
            setR(1);
            setNumSamp(16);
            
            // Create a 2-D array for converter raw word to word mapping
            ng_data = (uint64_t**) malloc(getM() * sizeof(uint64_t));

            for ( int i = 0; i < getM(); i++) {
                ng_data[i] = (uint64_t*) malloc(num_samples * sizeof(uint64_t));
            } 
        }

        JesdTl ( uint32_t L, uint32_t M, uint32_t Np, uint32_t R, int num_samples) {
            setL ( L );
            setM ( M );
            setNp ( Np );
            setR ( R );
            setNumSamp ( num_samples );

            // Create a 2-D array for converter raw word to word mapping
            ng_data = (uint64_t**) malloc(getM() * sizeof(uint64_t));

            for ( int i = 0; i < getM(); i++) {
                ng_data[i] = (uint64_t*) malloc(num_samples * sizeof(uint64_t));
            } 
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

            col: Number of columns which is the number of samples (valid or invalid). This should be the same for both
                raw_conv_data and word_data.
            
            conv_prec: Precision of the converters (12 or 16)

            ng_data: This is the output of this function. Samples in the raw_conv_data array will be expanded to Np. 
                The number of rows in this array will be known apriori (equal to M x P).
        */
        void map_cw_2_w ( uint16_t** raw_conv_data ) {
            int num_row = M * P;

            for ( int r = 0; r < num_row; r ++ ) {
                for ( int c = 0; c < num_samples; c ++) {
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
                    cout << hex  << setw(18) << ng_data[m][s] << " ";
                }
                cout << endl;
            }   

        }  

        void gen_output ( uint16_t** inp_data ) {

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

void gen_conv_data(uint16_t** inp_data, int row, int col, int R) {
    
    // Now initialize the input data with random values
    for ( int m = 0; m < row; m ++ ) {
        for ( int s = 0; s < col; s ++ ) {
            //Based on the rate we put samples only in
            //needed locations
            switch ( R ) {
                case 1: { // 122.88 MSps
                    if(s%4 == 0)
                        inp_data[m][s] = rand();
                    else 
                        inp_data[m][s] = 0;
                    break; 
                }

                case 2: { // 
                    if(s%2 == 0)
                        inp_data[m][s] = rand();
                    else 
                        inp_data[m][s] = 0; 
                    break;
                }

                case 3: case 6: {
                    if(s%4 == 0 || s%4 == 1 || s%4 == 2) 
                        inp_data[m][s] = rand();
                    else 
                        inp_data[m][s] = 0; 
                    break;
                }

                case 4: case 8: {
                    inp_data[m][s] = rand();
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
    uint32_t M = 2;
    // Precision
    uint32_t Np = 48;
    // Rate
    uint32_t R = 3;
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
    inp_data = (uint16_t**) malloc(tlobj.getM() * sizeof(uint16_t));

    for ( int i = 0; i < tlobj.getM(); i++) {
        inp_data[i] = (uint16_t*) malloc(adj_num_samp * sizeof(uint16_t));
    } 

    // Generate random input data
    gen_conv_data ( inp_data, tlobj.getM(), adj_num_samp, tlobj.getR());

    // Print this input array for debug.
    cout << showbase << internal << setfill('0');
    // Now print all the samples 
    for ( int m = 0; m < tlobj.getM(); m ++ ) {
        for ( int s = 0; s < adj_num_samp; s ++ ) {
            cout << hex  << setw(6) << inp_data[m][s] << " ";
        }
        cout << endl;
    }

    tlobj.map_cw_2_w( inp_data );

    /*
    cout << "Number of arguments: " << argc << endl;
    switch ( argc ) {
        case 1: { // Default case. No parameters given
            break;
        }
        default: {
            JesdTl tlobj;
            break;
        }
    }
    */

    cout << "Number of Lanes: " << tlobj.getM() << endl;

    free(inp_data);

    return 0;
}
