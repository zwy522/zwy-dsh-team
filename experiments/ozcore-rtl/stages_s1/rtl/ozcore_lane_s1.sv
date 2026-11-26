// Single-modulus lane: preprocess low byte -> K=128 MAC column -> postprocess bypass.
module ozcore_lane_s1 #(parameter int K=128) (
    input  logic clk, rst,
    input  logic in_valid,
    input  logic [K*16-1:0] weight_pkg,
    input  logic [K*16-1:0] act_pkg,
    input  logic out_ready,
    output logic out_valid,
    output logic signed [31:0] out_acc,
    output logic in_ready
);
    logic w_pre_valid, a_pre_valid;
    logic [K*8-1:0] w_pre, a_pre;
    logic signed [31:0] mac_acc;
    logic post_valid;
    logic signed [31:0] post_acc;
    logic w_ready, a_ready;

    ozcore_preprocess_s1 #(.K(K)) u_wpre (
        .clk(clk), .rst(rst), .in_valid(in_valid), .in_data(weight_pkg),
        .out_ready(w_ready), .out_valid(w_pre_valid), .out_data(w_pre), .in_ready()
    );
    ozcore_preprocess_s1 #(.K(K)) u_apre (
        .clk(clk), .rst(rst), .in_valid(in_valid), .in_data(act_pkg),
        .out_ready(a_ready), .out_valid(a_pre_valid), .out_data(a_pre), .in_ready()
    );
    assign w_ready = 1'b1; // both preprocess blocks advance together
    assign a_ready = 1'b1;
    assign in_ready = w_ready & a_ready;

    ozcore_mac_col_s1 #(.K(K)) u_mac (.weight_flat(w_pre), .data_flat(a_pre), .acc(mac_acc));

    ozcore_postprocess_s1 #(.K(1)) u_post (
        .clk(clk), .rst(rst), .in_valid(w_pre_valid & a_pre_valid),
        .in_acc(mac_acc), .out_ready(out_ready), .out_valid(post_valid),
        .out_data(post_acc), .in_ready()
    );
    assign out_valid = post_valid;
    assign out_acc = post_acc;
endmodule
