`timescale 1ns / 1ps
module fp16_mac (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        valid_in,
    input  wire        clear,
    input  wire [15:0] a,
    input  wire [15:0] b,
    output wire [31:0] acc,
    output wire        valid_out
);
    fp_mac #(.SIG_W(11), .EXP_W(5), .BIAS(15)) u (
        .clk(clk), .rst_n(rst_n), .valid_in(valid_in), .clear(clear),
        .a(a), .b(b), .acc(acc), .valid_out(valid_out)
    );
endmodule
