// Single-modulus INT8 MAC column: K=128 dot product.
module ozcore_mac_col_s1 #(parameter int K=128) (
    input  logic signed [K*8-1:0] weight_flat,
    input  logic signed [K*8-1:0] data_flat,
    output logic signed [31:0] acc
);
    always_comb begin
        acc = 32'sd0;
        for (int j=0; j<K; j++)
            acc = acc + $signed(weight_flat[j*8 +: 8]) * $signed(data_flat[j*8 +: 8]);
    end
endmodule
