// Single-modulus INT8 preprocess: low byte of each 16-bit int slot.
module ozcore_preprocess_s1 #(parameter int K=128) (
    input  logic clk, rst,
    input  logic in_valid,
    input  logic [K*16-1:0] in_data,
    input  logic out_ready,
    output logic out_valid,
    output logic [K*8-1:0] out_data,
    output logic in_ready
);
    assign in_ready = ~out_valid | out_ready;
    always_ff @(posedge clk) begin
        if (rst) begin
            out_valid <= 1'b0;
            out_data <= '0;
        end else if (in_valid && in_ready) begin
            for (int i=0; i<K; i++) out_data[i*8 +: 8] <= in_data[i*16 +: 8];
            out_valid <= 1'b1;
        end else if (out_valid && out_ready) begin
            out_valid <= 1'b0;
        end
    end
endmodule
