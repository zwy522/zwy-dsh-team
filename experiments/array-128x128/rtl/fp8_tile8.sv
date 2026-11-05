`timescale 1ns / 1ps
module fp8_tile8 (
    input wire clk, rst_n, valid_in, clear,
    input wire [511:0] a_flat, b_flat,
    output wire [2047:0] acc_flat, output wire valid_out
);
    fp_tile8_array #(.SIG_W(4), .EXP_W(4), .BIAS(7)) u (
        .clk(clk), .rst_n(rst_n), .valid_in(valid_in), .clear(clear),
        .a_flat(a_flat), .b_flat(b_flat), .acc_flat(acc_flat), .valid_out(valid_out)
    );
endmodule
