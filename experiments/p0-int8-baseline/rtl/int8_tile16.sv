// P0b: 16x16 weight-stationary INT8 tile with shared control and tree reduction.
// One output per row per cycle; 16 x 32-bit accumulators (not one per multiplier).
// This is the optimized contrast to the flat per-lane int8_mac baseline.

`timescale 1ns / 1ps

module int8_tile16 (
    input  wire               clk,
    input  wire               rst_n,

    // Weight load: 16 rows, 16 INT8 each.
    input  wire               load,
    input  wire [3:0]         load_row,
    input  wire [127:0]       wdata_flat,

    // Compute: x vector, 16 INT8.
    input  wire               valid_in,
    input  wire [127:0]       x_flat,

    output wire               valid_out,
    output wire [511:0]       y_flat
);

    // Weight memory: 16 rows x 16 cols, INT8.
    reg signed [7:0] wmem [0:255];

    // S0: input register.
    reg signed [7:0] x_reg [0:15];

    // S1: 256 products.
    reg signed [15:0] p [0:255];

    // S2-S5: reduction tree.
    reg signed [16:0] l1 [0:127];
    reg signed [17:0] l2 [0:63];
    reg signed [18:0] l3 [0:31];
    reg signed [19:0] l4 [0:15];

    // S6: accumulators.
    reg signed [31:0] acc [0:15];

    reg v1, v2, v3, v4, v5, v6, v7;

    integer i, j, ai;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            v1 <= 1'b0; v2 <= 1'b0; v3 <= 1'b0;
            v4 <= 1'b0; v5 <= 1'b0; v6 <= 1'b0; v7 <= 1'b0;
            for (i = 0; i < 16; i = i + 1) begin
                x_reg[i] <= 8'sd0;
                l4[i]    <= 20'sd0;
                acc[i]   <= 32'sd0;
            end
            for (i = 0; i < 256; i = i + 1)
                p[i] <= 16'sd0;
            for (i = 0; i < 128; i = i + 1)
                l1[i] <= 17'sd0;
            for (i = 0; i < 64; i = i + 1)
                l2[i] <= 18'sd0;
            for (i = 0; i < 32; i = i + 1)
                l3[i] <= 19'sd0;
        end else begin
            // Weight load.
            if (load) begin
                for (j = 0; j < 16; j = j + 1)
                    wmem[load_row*16 + j] <= wdata_flat[j*8 +: 8];
            end

            // S0: input register.
            for (j = 0; j < 16; j = j + 1)
                x_reg[j] <= x_flat[j*8 +: 8];

            // S1: 256 products.
            v1 <= valid_in & ~load;
            for (i = 0; i < 16; i = i + 1)
                for (j = 0; j < 16; j = j + 1)
                    p[i*16 + j] <= x_reg[j] * wmem[i*16 + j];

            // S2: L1 (16 -> 8).
            v2 <= v1;
            for (i = 0; i < 16; i = i + 1)
                for (j = 0; j < 8; j = j + 1)
                    l1[i*8 + j] <= p[i*16 + 2*j] + p[i*16 + 2*j + 1];

            // S3: L2 (8 -> 4).
            v3 <= v2;
            for (i = 0; i < 16; i = i + 1)
                for (j = 0; j < 4; j = j + 1)
                    l2[i*4 + j] <= l1[i*8 + 2*j] + l1[i*8 + 2*j + 1];

            // S4: L3 (4 -> 2).
            v4 <= v3;
            for (i = 0; i < 16; i = i + 1)
                for (j = 0; j < 2; j = j + 1)
                    l3[i*2 + j] <= l2[i*4 + 2*j] + l2[i*4 + 2*j + 1];

            // S5: L4 (2 -> 1).
            v5 <= v4;
            for (i = 0; i < 16; i = i + 1)
                l4[i] <= l3[i*2] + l3[i*2 + 1];

            // S6: l4 is valid when v6 is high; v7 marks the accumulator output.
            v6 <= v5;
            v7 <= v6;
            if (v6) begin
                for (i = 0; i < 16; i = i + 1)
                    acc[i] <= acc[i] + l4[i];
            end
        end
    end

    assign valid_out = v7;
    genvar gi;
    generate
        for (gi = 0; gi < 16; gi = gi + 1) begin : g_y
            assign y_flat[gi*32 +: 32] = acc[gi];
        end
    endgenerate

endmodule
