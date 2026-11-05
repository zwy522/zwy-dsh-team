// P0 baseline: replicated N x N array of int8_mac lanes.
// The wrapper is intentionally simple (no cross-lane reduction) so that
// synthesis area per lane and its scaling can be measured directly.

`timescale 1ns / 1ps

module int8_array #(
    parameter integer N = 4,
    parameter integer ACC_W = 32
) (
    input  wire              clk,
    input  wire              rst_n,
    input  wire              valid_in,
    input  wire              acc_clear,
    input  wire [N*8-1:0]    a_flat,
    input  wire [N*8-1:0]    b_flat,
    output wire [N*ACC_W-1:0] acc_flat,
    output wire              valid_out
);

    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin : g_lane
            wire signed [7:0] a_i;
            wire signed [7:0] b_i;
            wire signed [ACC_W-1:0] acc_i;
            wire v_i;

            assign a_i = a_flat[i*8 +: 8];
            assign b_i = b_flat[i*8 +: 8];

            int8_mac #(.ACC_W(ACC_W)) u_mac (
                .clk(clk),
                .rst_n(rst_n),
                .valid_in(valid_in),
                .acc_clear(acc_clear),
                .a(a_i),
                .b(b_i),
                .acc(acc_i),
                .valid_out(v_i)
            );

            assign acc_flat[i*ACC_W +: ACC_W] = acc_i;
        end
    endgenerate

    // All lanes share the same pipeline; use lane 0's delayed valid.
    assign valid_out = g_lane[0].v_i;

endmodule
