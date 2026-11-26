`timescale 1ns/1ps
module tb_ozcore_simd_int8;
    localparam int K = 8;
    localparam int S = 12;
    localparam int W = S*K*8;
    localparam int AW = S*32;
    localparam int SW = S*9;

    logic signed [W-1:0] weight_flat, data_flat;
    logic signed [SW-1:0] e_flat, shift_in_flat;
    logic signed [AW-1:0] acc_flat;
    logic signed [SW-1:0] shift_out_flat;

    ozcore_simd_int8 #(.K(K), .S_MAX(S)) dut (
        .weight_flat(weight_flat), .data_flat(data_flat),
        .e_flat(e_flat), .shift_in_flat(shift_in_flat),
        .acc_flat(acc_flat), .shift_out_flat(shift_out_flat)
    );

    integer fd, n, cases, errors;
    logic signed [AW-1:0] exp_acc;
    logic signed [SW-1:0] exp_sh;

    initial begin
        cases = 0; errors = 0;
        fd = $fopen("vectors.txt", "r");
        if (fd == 0) begin $display("ERROR: cannot open vectors.txt"); $fatal; end
        while (!$feof(fd)) begin
            n = $fscanf(fd, "%h %h %h %h %h %h\n", weight_flat, data_flat, e_flat, shift_in_flat, exp_acc, exp_sh);
            if (n != 6) break;
            #1;
            cases++;
            if (acc_flat !== exp_acc) begin
                errors++;
                $display("ACC MISMATCH case %0d: got %h exp %h", cases, acc_flat, exp_acc);
                if (errors > 5) $fatal;
            end
            if (shift_out_flat !== exp_sh) begin
                errors++;
                $display("SHIFT MISMATCH case %0d: got %h exp %h", cases, shift_out_flat, exp_sh);
                if (errors > 5) $fatal;
            end
        end
        $fclose(fd);
        $display("SIMD_INT8: cases=%0d errors=%0d", cases, errors);
        if (errors == 0) $display("SIMD_INT8: PASS");
        else $display("SIMD_INT8: FAIL");
        $finish;
    end
endmodule
