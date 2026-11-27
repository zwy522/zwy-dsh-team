// OzCore INT8 SIMD engine, reduced-parameter RTL reimplementation.
// Function: for each of S_MAX moduli, acc = sum_j weight[j]*data[j] (signed INT8),
// shift_out = e_reg + shift_in.  This matches the HLS simd_engine_core INT8 path.
module ozcore_simd_int8 #(
    parameter int K = 8,
    parameter int S_MAX = 12
) (
    input  logic signed [S_MAX*K*8-1:0] weight_flat,
    input  logic signed [S_MAX*K*8-1:0] data_flat,
    input  logic signed [S_MAX*9-1:0]   e_flat,
    input  logic signed [S_MAX*9-1:0]   shift_in_flat,
    output logic signed [S_MAX*32-1:0]  acc_flat,
    output logic signed [S_MAX*9-1:0]   shift_out_flat
);
    logic signed [31:0] acc [S_MAX];
    logic signed [8:0]  shift_out [S_MAX];

    always_comb begin
        for (int i = 0; i < S_MAX; i++) begin
            acc[i] = 32'sd0;
            for (int j = 0; j < K; j++) begin
                acc[i] = acc[i] + $signed(weight_flat[(i*K+j)*8 +: 8]) * $signed(data_flat[(i*K+j)*8 +: 8]);
            end
            shift_out[i] = e_flat[i*9 +: 9] + shift_in_flat[i*9 +: 9];
        end
    end

    generate
        for (genvar i = 0; i < S_MAX; i++) begin : g_pack
            assign acc_flat[i*32 +: 32] = acc[i];
            assign shift_out_flat[i*9 +: 9] = shift_out[i];
        end
    endgenerate
endmodule
