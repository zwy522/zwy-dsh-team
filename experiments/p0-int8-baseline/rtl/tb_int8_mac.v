// P0 functional smoke test for int8_mac (directed cases, VCS).
`timescale 1ns / 1ps

module tb_int8_mac;
    reg clk = 0;
    reg rst_n = 0;
    reg valid_in = 0;
    reg acc_clear = 0;
    reg signed [7:0] a = 0;
    reg signed [7:0] b = 0;
    wire signed [31:0] acc;
    wire valid_out;

    int8_mac dut (
        .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
        .acc_clear(acc_clear), .a(a), .b(b),
        .acc(acc), .valid_out(valid_out)
    );

    always #5 clk = ~clk;

    task apply(input signed [7:0] aa, input signed [7:0] bb, input clr);
        begin
            @(negedge clk);
            a = aa; b = bb; valid_in = 1'b1; acc_clear = clr;
            @(negedge clk);
            valid_in = 1'b0; acc_clear = 1'b0;
        end
    endtask

    initial begin
        repeat (3) @(posedge clk);
        rst_n = 1;
        repeat (2) @(posedge clk);

        apply(8'sd3, 8'sd4, 1'b1);
        repeat (3) @(posedge clk);
        if (acc !== 32'sd12) begin
            $display("FAIL case1 acc=%0d expected 12", acc); $finish;
        end

        apply(-8'sd2, 8'sd5, 1'b0);
        repeat (3) @(posedge clk);
        if (acc !== 32'sd2) begin
            $display("FAIL case2 acc=%0d expected 2", acc); $finish;
        end

        apply(8'sd7, -8'sd3, 1'b0);
        repeat (3) @(posedge clk);
        if (acc !== -32'sd19) begin
            $display("FAIL case3 acc=%0d expected -19", acc); $finish;
        end

        $display("PASS int8_mac directed cases, acc=%0d", acc);
        $finish;
    end
endmodule
