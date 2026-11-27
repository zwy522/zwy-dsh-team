module ozcore_top_s1n128 (
    input  logic clk, rst, weight_valid,
    input  logic [$clog2(128)-1:0] weight_col,
    input  logic [1*128*16-1:0] weight_flat,
    input  logic act_valid,
    input  logic [1*128*16-1:0] act_flat,
    input  logic out_ready,
    output logic out_valid,
    output logic [1*128*32-1:0] out_flat,
    output logic weight_ready, act_ready
);
    ozcore_top_int8 #(.K(128), .N(128), .S_MAX(1)) u (
        .clk(clk), .rst(rst), .weight_valid(weight_valid), .weight_col(weight_col),
        .weight_flat(weight_flat), .act_valid(act_valid), .act_flat(act_flat),
        .out_ready(out_ready), .out_valid(out_valid), .out_flat(out_flat),
        .weight_ready(weight_ready), .act_ready(act_ready)
    );
endmodule
