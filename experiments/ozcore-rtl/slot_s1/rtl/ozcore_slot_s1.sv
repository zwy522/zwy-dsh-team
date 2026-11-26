// Complete single OzCore slot: INT8 MAC (12 lanes, K=128), preprocess,
// CRT + mod-P reduction, int2fp, valid handshake.
module ozcore_slot_s1 #(parameter int K=128, S_MAX=12) (
    input  logic clk, rst, in_valid,
    input  logic [S_MAX*K*16-1:0] weight_pkg,
    input  logic [S_MAX*K*16-1:0] act_pkg,
    input  logic out_ready,
    output logic out_valid,
    output logic [31:0] fp_out,
    output logic in_ready
);
    logic w_pre_valid, a_pre_valid, w_ready, a_ready;
    logic [S_MAX*K*8-1:0] w_pre, a_pre;
    logic signed [S_MAX*32-1:0] acc;
    logic signed [S_MAX*9-1:0] shift_out;
    logic signed [31:0] crt96;
    logic crt_valid;

    ozcore_preprocess_s1 #(.K(S_MAX*K)) u_wpre (
        .clk(clk), .rst(rst), .in_valid(in_valid), .in_data(weight_pkg),
        .out_ready(w_ready), .out_valid(w_pre_valid), .out_data(w_pre), .in_ready()
    );
    ozcore_preprocess_s1 #(.K(S_MAX*K)) u_apre (
        .clk(clk), .rst(rst), .in_valid(in_valid), .in_data(act_pkg),
        .out_ready(a_ready), .out_valid(a_pre_valid), .out_data(a_pre), .in_ready()
    );
    assign w_ready = 1'b1; assign a_ready = 1'b1;
    assign in_ready = 1'b1;

    ozcore_simd_int8_k128 u_mac (
        .weight_flat(w_pre), .data_flat(a_pre),
        .e_flat('0), .shift_in_flat('0),
        .acc_flat(acc), .shift_out_flat(shift_out)
    );

    ozcore_crt_int2fp_s1 u_post (
        .dots(acc), .fp_out(fp_out), .crt_out(crt96)
    );

    assign crt_valid = w_pre_valid & a_pre_valid;
    always_ff @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else if (crt_valid) out_valid <= 1'b1;
        else if (out_valid && out_ready) out_valid <= 1'b0;
    end
endmodule
