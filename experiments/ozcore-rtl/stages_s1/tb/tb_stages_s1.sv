`timescale 1ns/1ps
module tb_stages_s1;
    localparam int K=128;
    logic clk=0, rst=1;
    // preprocess
    logic pre_in_valid=0, pre_out_ready=1, pre_out_valid, pre_in_ready;
    logic [K*16-1:0] pre_in; logic [K*8-1:0] pre_out, pre_exp;
    // postprocess
    logic post_in_valid=0, post_out_ready=1, post_out_valid, post_in_ready;
    logic [K*32-1:0] post_in, post_out, post_exp;
    // mac
    logic signed [K*8-1:0] w, x; logic signed [31:0] mac_acc; logic [31:0] mac_exp;
    // lane
    logic lane_in_valid=0, lane_out_ready=1, lane_out_valid, lane_in_ready;
    logic [K*16-1:0] lane_w, lane_x; logic signed [31:0] lane_acc; logic [31:0] lane_exp;

    ozcore_preprocess_s1 #(.K(K)) u_pre (.clk(clk),.rst(rst),.in_valid(pre_in_valid),.in_data(pre_in),.out_ready(pre_out_ready),.out_valid(pre_out_valid),.out_data(pre_out),.in_ready(pre_in_ready));
    ozcore_postprocess_s1 #(.K(K)) u_post (.clk(clk),.rst(rst),.in_valid(post_in_valid),.in_acc(post_in),.out_ready(post_out_ready),.out_valid(post_out_valid),.out_data(post_out),.in_ready(post_in_ready));
    ozcore_mac_col_s1 #(.K(K)) u_mac (.weight_flat(w),.data_flat(x),.acc(mac_acc));
    ozcore_lane_s1 #(.K(K)) u_lane (.clk(clk),.rst(rst),.in_valid(lane_in_valid),.weight_pkg(lane_w),.act_pkg(lane_x),.out_ready(lane_out_ready),.out_valid(lane_out_valid),.out_acc(lane_acc),.in_ready(lane_in_ready));

    always #5 clk=~clk;
    integer fd, errs;
    initial begin
        errs=0; fd=$fopen("vectors.txt","r");
        if (!fd) $fatal;
        @(posedge clk); #1; rst=0; #1;
        // preprocess
        $fscanf(fd,"%h %h\n",pre_in,pre_exp); pre_in_valid=1; @(posedge clk); #1; pre_in_valid=0;
        if (!pre_out_valid || pre_out !== pre_exp) begin errs++; $display("PRE FAIL got=%h exp=%h valid=%b",pre_out,pre_exp,pre_out_valid); end
        // postprocess
        $fscanf(fd,"%h %h\n",post_in,post_exp); post_in_valid=1; @(posedge clk); #1; post_in_valid=0;
        if (!post_out_valid || post_out !== post_exp) begin errs++; $display("POST FAIL valid=%b",post_out_valid); end
        // mac
        $fscanf(fd,"%h %h %h\n",w,x,mac_exp); #1;
        if (mac_acc !== $signed(mac_exp)) begin errs++; $display("MAC FAIL got=%h exp=%h",mac_acc,mac_exp); end
        // lane
        $fscanf(fd,"%h %h %h\n",lane_w,lane_x,lane_exp); lane_in_valid=1; @(posedge clk); #1; lane_in_valid=0;
        repeat (1) @(posedge clk); #1;
        if (!lane_out_valid || lane_acc !== $signed(lane_exp)) begin errs++; $display("LANE FAIL got=%h exp=%h valid=%b",lane_acc,lane_exp,lane_out_valid); end
        $display("STAGES_S1: errors=%0d",errs);
        if (errs==0) $display("STAGES_S1: PASS"); else $display("STAGES_S1: FAIL");
        $finish;
    end
endmodule
