// 4-lane wrapper for the P0 array scaling experiment.
`timescale 1ns / 1ps

module int8_array_n4 (
    input  wire               clk,
    input  wire               rst_n,
    input  wire               valid_in,
    input  wire               acc_clear,
    input  wire [31:0]        a_flat,
    input  wire [31:0]        b_flat,
    output wire [127:0]       acc_flat,
    output wire               valid_out
);

    int8_array #(.N(4), .ACC_W(32)) u_array (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(valid_in),
        .acc_clear(acc_clear),
        .a_flat(a_flat),
        .b_flat(b_flat),
        .acc_flat(acc_flat),
        .valid_out(valid_out)
    );

endmodule
