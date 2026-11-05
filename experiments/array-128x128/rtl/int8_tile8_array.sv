// 8x8 array (64 lanes) of int8_mac, shared valid/clear, for array-level scaling.
`timescale 1ns / 1ps
module int8_tile8_array (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         valid_in,
    input  wire         acc_clear,
    input  wire [511:0] a_flat,
    input  wire [511:0] b_flat,
    output wire [2047:0] acc_flat,
    output wire         valid_out
);
    genvar i, j;
    generate
        for (i = 0; i < 8; i = i + 1) begin : g_row
            for (j = 0; j < 8; j = j + 1) begin : g_col
                wire signed [7:0] a_i = a_flat[(i*8+j)*8 +: 8];
                wire signed [7:0] b_i = b_flat[(i*8+j)*8 +: 8];
                wire signed [31:0] acc_i;
                wire v_i;
                int8_mac u_mac (
                    .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
                    .acc_clear(acc_clear), .a(a_i), .b(b_i),
                    .acc(acc_i), .valid_out(v_i)
                );
                assign acc_flat[(i*8+j)*32 +: 32] = acc_i;
                if (i == 0 && j == 0) assign valid_out = v_i;
            end
        end
    endgenerate
endmodule
