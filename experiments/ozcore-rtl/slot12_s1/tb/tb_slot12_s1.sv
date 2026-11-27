`timescale 1ns/1ps
module tb_slot12_s1;
    localparam int K=128;
    logic clk=0, rst=1, start=0, out_valid, busy;
    logic [K*8-1:0] w, x;
    logic [31:0] fp, exp_fp;
    integer fd, errs, case_i;
    ozcore_slot12_s1 #(.K(K)) dut(.clk(clk),.rst(rst),.start(start),.weight_flat(w),.act_flat(x),.out_valid(out_valid),.fp_out(fp),.busy(busy));
    always #5 clk=~clk;
    initial begin
        errs=0; fd=$fopen("vectors.txt","r"); if(!fd) $fatal;
        @(posedge clk); #1; rst=0;
        for (case_i=0; case_i<5; case_i++) begin
            if ($fscanf(fd,"%h %h %h\n",w,x,exp_fp) != 3) $fatal;
            start=1; @(posedge clk); #1; start=0;
            repeat (25) @(posedge clk); #1;
            if (!out_valid || fp !== exp_fp) begin
                errs++; $display("SLOT12 FAIL case%0d valid=%b got=%h exp=%h",case_i,out_valid,fp,exp_fp);
            end
            repeat (2) @(posedge clk);
        end
        $display("SLOT12: errors=%0d",errs);
        if (errs==0) $display("SLOT12: PASS"); else $display("SLOT12: FAIL");
        $finish;
    end
endmodule
