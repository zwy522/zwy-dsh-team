// Full-length INT8 SIMD engine: K=128, S_MAX=12, 1536 signed multipliers.
module ozcore_simd_int8_k128 (
    input  logic signed [12*128*8-1:0] weight_flat,
    input  logic signed [12*128*8-1:0] data_flat,
    input  logic signed [12*9-1:0]    e_flat,
    input  logic signed [12*9-1:0]    shift_in_flat,
    output logic signed [12*32-1:0]   acc_flat,
    output logic signed [12*9-1:0]    shift_out_flat
);
    ozcore_simd_int8 #(.K(128), .S_MAX(12)) u_core (
        .weight_flat(weight_flat), .data_flat(data_flat),
        .e_flat(e_flat), .shift_in_flat(shift_in_flat),
        .acc_flat(acc_flat), .shift_out_flat(shift_out_flat)
    );
endmodule
