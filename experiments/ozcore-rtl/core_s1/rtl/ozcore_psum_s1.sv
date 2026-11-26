// Single-modulus psum/output register bank: N x 32-bit.
module ozcore_psum_s1 #(parameter int N=128) (
    input  logic clk, rst, wr_en,
    input  logic [N*32-1:0] acc,
    output logic [N*32-1:0] data
);
    always_ff @(posedge clk) begin
        if (rst) data <= '0;
        else if (wr_en) data <= acc;
    end
endmodule
