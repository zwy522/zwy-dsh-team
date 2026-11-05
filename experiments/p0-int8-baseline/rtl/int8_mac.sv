// P0 baseline: parameterized signed INT8 MAC lane with INT32 accumulator.
// 3-stage pipeline: operand register -> multiply -> accumulate.
// This is a format-specific baseline for area/timing calibration, not the
// full OzCore pre/post-processing pipeline.

`timescale 1ns / 1ps

module int8_mac #(
    parameter integer ACC_W = 32
) (
    input  wire              clk,
    input  wire              rst_n,
    input  wire              valid_in,
    input  wire              acc_clear,
    input  wire signed [7:0] a,
    input  wire signed [7:0] b,
    output reg  signed [ACC_W-1:0] acc,
    output reg               valid_out
);

    // Stage 1: operand and control registers.
    reg signed [7:0] a_s1;
    reg signed [7:0] b_s1;
    reg              v_s1;
    reg              clear_s1;

    // Stage 2: product.
    wire signed [15:0] prod_comb;
    reg signed [15:0] prod_s2;
    reg signed [ACC_W-1:0] prod_ext_s2;
    reg              v_s2;
    reg              clear_s2;

    assign prod_comb = a_s1 * b_s1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_s1     <= 8'sd0;
            b_s1     <= 8'sd0;
            v_s1     <= 1'b0;
            clear_s1 <= 1'b0;
            prod_s2  <= 16'sd0;
            prod_ext_s2 <= {ACC_W{1'b0}};
            v_s2     <= 1'b0;
            clear_s2 <= 1'b0;
            acc      <= {ACC_W{1'b0}};
            valid_out <= 1'b0;
        end else begin
            // S1
            a_s1     <= a;
            b_s1     <= b;
            v_s1     <= valid_in;
            clear_s1 <= acc_clear;

            // S2
            prod_s2  <= prod_comb;
            // Sign-extend the 16-bit product to the accumulator width.
            prod_ext_s2 <= {{(ACC_W-16){prod_comb[15]}}, prod_comb};
            v_s2     <= v_s1;
            clear_s2 <= clear_s1;

            // S3: accumulate only on a valid MAC. A clear with valid loads
            // the first product; a clear without valid zeroes the accumulator.
            if (clear_s2)
                acc <= v_s2 ? prod_ext_s2 : {ACC_W{1'b0}};
            else if (v_s2)
                acc <= acc + prod_ext_s2;
            valid_out <= v_s2;
        end
    end

endmodule
