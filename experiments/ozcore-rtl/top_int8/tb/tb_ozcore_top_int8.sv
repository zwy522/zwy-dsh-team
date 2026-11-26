`timescale 1ns/1ps
module tb_ozcore_top_int8;
    localparam int K=128, N=2, S=12;
    localparam int INW=S*K*16, OUTW=S*N*32;
    logic clk=0, rst=1, weight_valid=0, act_valid=0;
    logic [$clog2(N)-1:0] weight_col;
    logic [INW-1:0] weight_flat, act_flat;
    logic [OUTW-1:0] out_flat;
    logic out_valid;

    ozcore_top_int8 #(.K(K),.N(N),.S_MAX(S)) dut (.*);

    always #5 clk = ~clk;
    integer fd, n, errs;
    logic [INW-1:0] wtmp, xtmp;
    logic [OUTW-1:0] exp_out;

    initial begin
        errs=0;
        fd=$fopen("vectors.txt","r");
        if (fd==0) begin $display("cannot open vectors"); $fatal; end
        @(posedge clk); #1; rst=0;
        for (n=0; n<N; n++) begin
            if ($fscanf(fd,"%h\n",wtmp) != 1) $fatal;
            weight_col=n; weight_flat=wtmp; weight_valid=1;
            @(posedge clk); #1; weight_valid=0;
        end
        for (n=0; n<5; n++) begin
            if ($fscanf(fd,"%h\n",xtmp) != 1) $fatal;
            if ($fscanf(fd,"%h\n",exp_out) != 1) $fatal;
            act_flat=xtmp; act_valid=1;
            @(posedge clk); #1; act_valid=0;
            if (!out_valid || out_flat !== exp_out) begin
                errs++;
                $display("MISMATCH case %0d out_valid=%b\n got=%h\n exp=%h", n, out_valid, out_flat, exp_out);
            end
        end
        $display("TOP_INT8: cases=5 errors=%0d", errs);
        if (errs==0) $display("TOP_INT8: PASS"); else $display("TOP_INT8: FAIL");
        $finish;
    end
endmodule
