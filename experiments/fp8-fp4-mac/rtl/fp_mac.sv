// Parameterized format-native FP MAC with FP32 accumulation.
// The product of two b-bit significands (including hidden) is normalized to
// FP32 and added to the accumulator with DesignWare DW_fp_add.
// Subnormals/NaN are not modeled; zero operands produce zero.

`timescale 1ns / 1ps

module fp_mac #(
    parameter integer SIG_W = 4,   // significand bits including hidden
    parameter integer EXP_W = 4,   // exponent bits
    parameter integer BIAS  = 7
) (
    input  wire                     clk,
    input  wire                     rst_n,
    input  wire                     valid_in,
    input  wire                     clear,
    input  wire [EXP_W+SIG_W-1:0]   a,
    input  wire [EXP_W+SIG_W-1:0]   b,
    output wire [31:0]              acc,
    output wire                     valid_out
);

    // ---- decode ----
    wire sa = a[EXP_W+SIG_W-1];
    wire sb = b[EXP_W+SIG_W-1];
    wire [EXP_W-1:0] ea_f = a[EXP_W+SIG_W-2 -: EXP_W];
    wire [EXP_W-1:0] eb_f = b[EXP_W+SIG_W-2 -: EXP_W];
    wire [SIG_W-2:0] ma = a[SIG_W-2:0];
    wire [SIG_W-2:0] mb = b[SIG_W-2:0];
    wire za = (ea_f == 0);
    wire zb = (eb_f == 0);

    wire signed [7:0] ea = $signed({1'b0, ea_f}) - BIAS;
    wire signed [7:0] eb = $signed({1'b0, eb_f}) - BIAS;
    wire [SIG_W-1:0] siga = {1'b1, ma};
    wire [SIG_W-1:0] sigb = {1'b1, mb};
    wire [2*SIG_W-1:0] sigp = siga * sigb;

    // Leading-one position of the product (combinational priority).
    reg [4:0] msb;
    integer k;
    always @* begin
        msb = 0;
        for (k = 0; k < 2*SIG_W; k = k + 1)
            if (sigp[k]) msb = k[4:0];
    end

    wire signed [8:0] expp = ea + eb + $signed({4'd0, msb}) - (2*(SIG_W-1));
    wire signed [9:0] e32s = expp + 127;
    wire [23:0] sig24 = sigp << (5'd23 - msb);

    wire [31:0] prod32 = (za | zb | (e32s <= 0) | (e32s >= 255)) ? 32'd0
                          : {sa ^ sb, e32s[7:0], sig24[22:0]};

    // ---- pipeline ----
    reg [31:0] prod_r;
    reg [31:0] acc_r;
    reg        v1, v2;

    wire [31:0] sum;
    DW_fp_add #(
        .sig_width(23), .exp_width(8), .ieee_compliance(0)
    ) u_add (
        .a(acc_r), .b(prod_r), .rnd(3'b000), .z(sum), .status()
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prod_r <= 32'd0;
            acc_r  <= 32'd0;
            v1 <= 1'b0;
            v2 <= 1'b0;
        end else begin
            prod_r <= prod32;
            v1 <= valid_in;
            if (clear)
                acc_r <= 32'd0;
            else if (v1)
                acc_r <= sum;
            v2 <= v1;
        end
    end

    assign acc = acc_r;
    assign valid_out = v2;

endmodule
