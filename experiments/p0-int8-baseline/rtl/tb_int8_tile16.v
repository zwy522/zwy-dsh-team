// P0b smoke test: load all-ones weights, drive x=1 then x=2, check y0=16/32.
`timescale 1ns / 1ps

module tb_int8_tile16;
    reg clk = 0;
    reg rst_n = 0;
    reg load = 0;
    reg [3:0] load_row = 0;
    reg [127:0] wdata_flat = 0;
    reg valid_in = 0;
    reg [127:0] x_flat = 0;
    wire valid_out;
    wire [511:0] y_flat;

    int8_tile16 dut (
        .clk(clk), .rst_n(rst_n), .load(load), .load_row(load_row),
        .wdata_flat(wdata_flat), .valid_in(valid_in), .x_flat(x_flat),
        .valid_out(valid_out), .y_flat(y_flat)
    );

    always #5 clk = ~clk;

    integer i, k;
    initial begin
        repeat (3) @(posedge clk);
        rst_n = 1;
        // Load all-ones weights.
        for (i = 0; i < 16; i = i + 1) begin
            @(negedge clk);
            load = 1; load_row = i; wdata_flat = {16{8'sd1}};
        end
        @(negedge clk);
        load = 0;
        // Drive x=1 for one cycle.
        valid_in = 1; x_flat = {16{8'sd1}};
        @(negedge clk);
        valid_in = 0;
        // Wait for the 6-stage pipeline.
        repeat (8) @(posedge clk);
        if (y_flat[31:0] !== 32'sd16) begin
            $display("FAIL y0=%0d expected 16", y_flat[31:0]); $finish;
        end
        // x=2 -> y0 should add 32.
        valid_in = 1; x_flat = {16{8'sd2}};
        @(negedge clk);
        valid_in = 0;
        repeat (8) @(posedge clk);
        if (y_flat[31:0] !== 32'sd48) begin
            $display("FAIL y0=%0d expected 48", y_flat[31:0]); $finish;
        end
        $display("PASS int8_tile16, y0=%0d", y_flat[31:0]);
        $finish;
    end
endmodule
