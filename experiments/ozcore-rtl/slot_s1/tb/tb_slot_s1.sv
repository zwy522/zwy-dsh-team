`timescale 1ns/1ps
module tb_slot_s1;
    localparam int K=128, S=12;
    logic clk=0, rst=1, in_valid=0, out_ready=1, out_valid, in_ready;
    logic [S*K*16-1:0] wpkg, xpkg;
    logic [31:0] fp, exp_fp;
    integer fd, errs, case_i;
    ozcore_slot_s1 #(.K(K),.S_MAX(S)) dut (.clk(clk),.rst(rst),.in_valid(in_valid),.weight_pkg(wpkg),.act_pkg(xpkg),.out_ready(out_ready),.out_valid(out_valid),.fp_out(fp),.in_ready(in_ready));
    always #5 clk=~clk;
    initial begin
        errs=0; fd=$fopen("vectors.txt","r"); if(!fd) $fatal;
        @(posedge clk); #1; rst=0;
        for (case_i=0; case_i<5; case_i++) begin
            if ($fscanf(fd,"%h %h %h\n",wpkg,xpkg,exp_fp) != 3) $fatal;
            in_valid=1; @(posedge clk); #1; in_valid=0;
            repeat (1) @(posedge clk); #1;
            if (!out_valid || fp !== exp_fp) begin
                errs++; $display("SLOT FAIL case%0d valid=%b got=%h exp=%h",case_i,out_valid,fp,exp_fp);
            end
            repeat (2) @(posedge clk);
        end
        $display("SLOT_FULL: errors=%0d",errs);
        if (errs==0) $display("SLOT_FULL: PASS"); else $display("SLOT_FULL: FAIL");
        $finish;
    end
endmodule
