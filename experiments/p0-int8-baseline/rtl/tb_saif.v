// Random-activity testbench used to produce a SAIF for DC power annotation.
`timescale 1ns / 1ps

module tb_saif;
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

    integer i;
    initial begin
        $set_toggle_region(tb_saif.dut);
        repeat (3) @(posedge clk);
        rst_n = 1;
        repeat (2) @(posedge clk);
        $toggle_start;
        for (i = 0; i < 20000; i = i + 1) begin
            @(negedge clk);
            a = $random;
            b = $random;
            valid_in = 1'b1;
            acc_clear = (i % 97 == 0);
            @(negedge clk);
            valid_in = 1'b0;
            acc_clear = 1'b0;
            @(negedge clk);
        end
        $toggle_stop;
        $toggle_report("int8_mac.saif", 1.0, "tb_saif.dut");
        $display("SAIF done, acc=%0d", acc);
        $finish;
    end
endmodule
