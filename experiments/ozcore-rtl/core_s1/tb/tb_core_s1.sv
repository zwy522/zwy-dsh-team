`timescale 1ns/1ps
module tb_core_s1;
    localparam int N=128, K=128;
    logic clk=0, rst=1;
    logic wr_en=0, psum_wr=0, al_in_valid=0, al_out_ready=1;
    logic [$clog2(N)-1:0] wr_col=0, rd_col=0;
    logic [K*8-1:0] wdata='0, rdata;
    logic [N*32-1:0] acc='0, pdata, al_in='0, al_out;
    logic al_out_valid, al_in_ready;
    logic start=0, c_wr, c_psum, c_out, c_busy, c_done;

    ozcore_weight_mem_s1 #(.N(N),.K(K)) u_wm (.clk(clk),.wr_en(wr_en),.wr_col(wr_col),.wr_data(wdata),.rd_col(rd_col),.rd_data(rdata));
    ozcore_psum_s1 #(.N(N)) u_psum (.clk(clk),.rst(rst),.wr_en(psum_wr),.acc(acc),.data(pdata));
    ozcore_aligner_s1 #(.N(N)) u_al (.clk(clk),.rst(rst),.in_valid(al_in_valid),.in_data(al_in),.out_ready(al_out_ready),.out_valid(al_out_valid),.out_data(al_out),.in_ready(al_in_ready));
    ozcore_control_s1 u_ctl (.clk(clk),.rst(rst),.start(start),.weight_wr_en(c_wr),.psum_wr_en(c_psum),.out_valid(c_out),.busy(c_busy),.done(c_done));

    always #5 clk=~clk;
    integer errs=0;
    initial begin
        @(posedge clk); #1; rst=0;
        // weight write/read
        wdata='hA5; wr_col=5; wr_en=1; @(posedge clk); #1; wr_en=0; rd_col=5; #1;
        if (rdata !== 'hA5) begin errs++; $display("WM FAIL %h",rdata); end
        // psum
        acc={N{32'h12345678}}; psum_wr=1; @(posedge clk); #1; psum_wr=0;
        if (pdata !== {N{32'h12345678}}) begin errs++; $display("PSUM FAIL"); end
        // aligner
        al_in={N{32'hDEADBEEF}}; al_in_valid=1; @(posedge clk); #1; al_in_valid=0;
        if (!al_out_valid || al_out !== {N{32'hDEADBEEF}}) begin errs++; $display("ALIGN FAIL"); end
        // control sequence
        start=1; @(posedge clk); #1; start=0;
        if (!c_wr) begin errs++; $display("CTRL LOAD FAIL"); end
        @(posedge clk); #1; @(posedge clk); #1; @(posedge clk); #1;
        $display("CORE_S1: errors=%0d",errs);
        if (errs==0) $display("CORE_S1: PASS"); else $display("CORE_S1: FAIL");
        $finish;
    end
endmodule
