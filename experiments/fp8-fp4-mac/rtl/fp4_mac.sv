`timescale 1ns / 1ps
module fp4_mac (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        valid_in,
    input  wire        clear,
    input  wire [3:0]  a,
    input  wire [3:0]  b,
    output wire [31:0] acc,
    output wire        valid_out
);
    fp_mac #(.SIG_W(2), .EXP_W(2), .BIAS(1)) u (
        .clk(clk), .rst_n(rst_n), .valid_in(valid_in), .clear(clear),
        .a(a), .b(b), .acc(acc), .valid_out(valid_out)
    );
endmodule
