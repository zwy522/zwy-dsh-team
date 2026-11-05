// 8x8 array (64 lanes) of fp_mac, shared valid/clear.
`timescale 1ns / 1ps
module fp_tile8_array #(
    parameter integer SIG_W = 4,
    parameter integer EXP_W = 4,
    parameter integer BIAS  = 7
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         valid_in,
    input  wire         clear,
    input  wire [64*(EXP_W+SIG_W)-1:0] a_flat,
    input  wire [64*(EXP_W+SIG_W)-1:0] b_flat,
    output wire [2047:0] acc_flat,
    output wire         valid_out
);
    genvar i, j;
    generate
        for (i = 0; i < 8; i = i + 1) begin : g_row
            for (j = 0; j < 8; j = j + 1) begin : g_col
                localparam integer W = EXP_W + SIG_W;
                wire [W-1:0] a_i = a_flat[(i*8+j)*W +: W];
                wire [W-1:0] b_i = b_flat[(i*8+j)*W +: W];
                wire [31:0] acc_i;
                wire v_i;
                fp_mac #(.SIG_W(SIG_W), .EXP_W(EXP_W), .BIAS(BIAS)) u_mac (
                    .clk(clk), .rst_n(rst_n), .valid_in(valid_in), .clear(clear),
                    .a(a_i), .b(b_i), .acc(acc_i), .valid_out(v_i)
                );
                assign acc_flat[(i*8+j)*32 +: 32] = acc_i;
                if (i == 0 && j == 0) assign valid_out = v_i;
            end
        end
    endgenerate
endmodule
