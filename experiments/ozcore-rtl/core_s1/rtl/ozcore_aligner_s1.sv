// Single-modulus output aligner: N x 32-bit registered output.
module ozcore_aligner_s1 #(parameter int N=128) (
    input  logic clk, rst, in_valid,
    input  logic [N*32-1:0] in_data,
    input  logic out_ready,
    output logic out_valid,
    output logic [N*32-1:0] out_data,
    output logic in_ready
);
    assign in_ready = ~out_valid | out_ready;
    always_ff @(posedge clk) begin
        if (rst) begin out_valid <= 1'b0; out_data <= '0; end
        else if (in_valid && in_ready) begin out_data <= in_data; out_valid <= 1'b1; end
        else if (out_valid && out_ready) out_valid <= 1'b0;
    end
endmodule
